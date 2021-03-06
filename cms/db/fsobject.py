#!/usr/bin/env python2
# -*- coding: utf-8 -*-

# Programming contest management system
# Copyright © 2010-2013 Giovanni Mascellani <mascellani@poisson.phc.unipi.it>
# Copyright © 2010-2012 Stefano Maggiolo <s.maggiolo@gmail.com>
# Copyright © 2010-2012 Matteo Boscariol <boscarim@hotmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""SQLAlchemy interfaces to store files in the database.

"""

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm.exc import NoResultFound

import psycopg2
from psycopg2 import OperationalError, InternalError

from . import Base, get_psycopg2_connection

from contextlib import contextmanager


class LargeObject:
    """Class to present a PostgreSQL large object as a Python file.

    A LargeObject mustn't be reused across transactions, but has to be
    created again.

    Because of technical reasons, this class has some restrictions
    that make it not fully compliant with usual file-like API. Be sure
    of checking the actual methods' docstring.

    """

    # Some constants from libpq, that are not published by psycopg2
    INV_READ = 0x20000
    INV_WRITE = 0x40000

    def __init__(self, loid, connection, mode):
        """Open a large object, creating it if required.

        Not to be called directly, but via FSObject.get_lobject().

        loid (int): the large object ID.
        connection (psycopg2.Connection): the connection to use.
        mode (str): how to open the file (r -> read, w -> write,
                    b -> binary, which must be always specified). If
                    None, use `rb'.

        """
        self.loid = loid
        self.connection = connection
        cursor = self.connection.cursor()

        # Check mode value
        mode = set(mode)
        if not (mode <= set(['r', 'w', 'b'])):
            raise ValueError("Only valid characters in mode are r, w and b")
        if 'b' not in mode:
            raise ValueError("Character b must be specified in mode")
        creat_mode = LargeObject.INV_READ | LargeObject.INV_WRITE
        # We always open at least in read mode
        open_mode = LargeObject.INV_READ | \
            (LargeObject.INV_WRITE if 'w' in mode else 0)

        # If the loid is 0, the the large object has to be created
        if self.loid == 0:
            cursor.execute("SELECT lo_creat(%(creat_mode)s);",
                           {'creat_mode': creat_mode})
            [self.loid] = cursor.fetchone()
            if self.loid == 0:
                raise OperationalError("Couldn't create large object")
            assert len(cursor.fetchall()) == 0

        # Open the file
        cursor.execute("SELECT lo_open(%(loid)s, %(open_mode)s);",
                            {'loid': self.loid,
                             'open_mode': open_mode})
        [self.fd] = cursor.fetchone()
        if self.fd == -1:
            raise OperationalError("Couldn't open large object")
        assert len(cursor.fetchall()) == 0

        cursor.close()

    def read(self, length):
        """Read bytes from the large object.

        Less bytes than requested may be read and returned.

        length (int): read no more than this number of bytes.

        return (string): the read data.

        """
        cursor = self.connection.cursor()
        cursor.execute("SELECT loread(%(fd)s, %(length)s);",
                            {'fd': self.fd,
                             'length': length})
        [data] = cursor.fetchone()
        assert len(cursor.fetchall()) == 0
        cursor.close()
        return bytes(data)

    def write(self, buf):
        """Write bytes to the large object.

        Less bytes then requested may be written.

        buf (string): data to write.

        return (int): number of written bytes.

        """
        cursor = self.connection.cursor()
        cursor.execute("SELECT lowrite(%(fd)s, %(buf)s);",
                            {'fd': self.fd,
                             'buf': psycopg2.Binary(buf)})
        [length] = cursor.fetchone()
        assert len(cursor.fetchall()) == 0
        cursor.close()
        if length == -1:
            raise OperationalError("Couldn't write in large object")
        return length

    def seek(self, offset, whence=0):
        """Move pointer to a location in large object.

        offset (int): offset from the reference point.
        whence (int): reference point, expressed like in os.seek().

        return (int): new position.

        """
        cursor = self.connection.cursor()
        cursor.execute("SELECT lo_lseek(%(fd)s, %(offset)s, %(whence)s);",
                       {'fd': self.fd,
                        'offset': offset,
                        'whence': whence})
        [pos] = cursor.fetchone()
        assert len(cursor.fetchall()) == 0
        cursor.close()
        if pos == -1:
            raise OperationalError("Couldn't seek in large object")
        return pos

    def tell(self):
        """Tell position in a large object.

        return (int): position in the large object.

        """
        cursor = self.connection.cursor()
        cursor.execute("SELECT lo_tell(%(fd)s);",
                       {'fd': self.fd})
        [pos] = cursor.fetchone()
        assert len(cursor.fetchall()) == 0
        cursor.close()
        if pos == -1:
            raise OperationalError("Couldn't tell large object")
        return pos

    def close(self):
        """Close the large object.

        After this call the object is not usable anymore. It is
        allowed to close an object more than once, with the calls
        after the first doing nothing.

        """
        # If the large object has already been closed, don't close it
        # again; this way the context manager doesn't risk to make
        # mistakes while exiting
        if self.fd is None:
            return

        cursor = self.connection.cursor()
        cursor.execute("SELECT lo_close(%(fd)s);",
                       {'fd': self.fd})
        [res] = cursor.fetchone()
        assert len(cursor.fetchall()) == 0
        cursor.close()

        # We delete the fd number to avoid writing on another file by
        # mistake
        self.fd = None

        if res == -1:
            raise OperationalError("Couldn't close large object")

    def unlink(self):
        """Delete the large object, removing its content.

        After an unlink, the content can't be restored anymore, so use
        with caution!

        If the large object is opened, it will be closed.

        """
        self.close()
        cursor = self.connection.cursor()
        cursor.execute("SELECT lo_unlink(%(loid)s);",
                       {'loid': self.loid})
        cursor.close()


class FSObject(Base):
    """Class to describe a file stored in the database.

    """

    __tablename__ = 'fsobjects'

    # Here we use the digest (SHA1 sum) of the file as primary key;
    # ideally al the columns that refer digests could be declared as
    # foreign keys against this column, but we intentiolally avoid
    # doing this to keep uncoupled the database and the file storage
    digest = Column(
        String,
        primary_key=True)

    # OID of the large object in the database
    loid = Column(
        Integer,
        nullable=False)

    # Human-readable description, primarily meant for debugging (i.e,
    # should have no semantic value from the viewpoint of CMS)
    description = Column(
        String,
        nullable=True)

    def __init__(self, digest=None, loid=0, description=None):
        self.digest = digest
        self.loid = loid
        self.description = description

    @contextmanager
    def get_lobject(self, session=None, mode=None):
        """Return an open file bounded to the represented large
        object. This is a context manager, so it should be used with
        the `with' clause this way:

          with fsobject.get_lobject() as lo:

        session (session object): the session to use, or None to use
                                  the one associated with the FSObject.
        mode (string): how to open the file (r -> read, w -> write,
                       b -> binary, which must be always
                       specified). If None, use `rb'.

        """
        if mode is None:
            mode = 'rb'
        if session is None:
            session = self.sa_session

        # Here we rely on the fact that we're using psycopg2 as
        # PostgreSQL backend
        connection = get_psycopg2_connection(session)
        lo = LargeObject(self.loid, connection, mode)

        if self.loid == 0:
            self.loid = lo.loid

        try:
            yield lo
        finally:
            # We ignore exceptions here, because they could be
            # triggered by trying to close a file descriptor when the
            # transaction already failed and cannot receive any more
            # commands; it's not grave if we can't close the fd: it
            # will be closed when the transaction terminates anyway
            try:
                lo.close()
            except InternalError:
                pass

    def check_lobject(self):
        """Check the large object availability in the database.

        Return True if this FSObject actually refers an object (that
        is, not the OID 0) and such large object exists. Returns False
        otherwise.

        """
        connection = get_psycopg2_connection(self.sa_session)
        if self.loid == 0:
            return False
        try:
            lo = LargeObject(self.loid, connection, 'rb')
        except OperationalError:
            return False
        else:
            lo.close()
            return True

    def delete(self):
        """Delete this file.

        """
        with self.get_lobject() as lo:
            lo.unlink()
        self.sa_session.delete(self)

    @classmethod
    def get_from_digest(cls, digest, session):
        """Return the FSObject with the specified digest, using the
        specified session.

        """
        try:
            return session.query(cls).filter(cls.digest == digest).one()
        except NoResultFound:
            return None

    @classmethod
    def get_all(cls, session):
        """Iterate over all the FSObjects available in the database.

        """
        if cls.__table__.exists():
            return session.query(cls)
        else:
            return []

    @classmethod
    def delete_all(cls, session):
        """Delete all files stored in the database. This cannot be
        undone. Large objects not linked by some FSObject cannot be
        detected at the moment, so they don't get deleted.

        """
        for fso in cls.get_all(session):
            fso.delete()
