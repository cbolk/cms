Installation
************

.. _installation_dependencies:

Dependencies
============

These are our requirements (in particular we highlight those that are not usually installed by default) - previous versions may or may not work:

* build environment for the programming languages allowed in the competition;

* `PostgreSQL <http://www.postgresql.org/>`_ >= 8.4;

* `gettext <http://www.gnu.org/software/gettext/>`_ >= 0.18;

* `Python <http://www.python.org/>`_ >= 2.7, < 3.0;

* `setuptools <http://pypi.python.org/pypi/setuptools>`_ >= 0.6;

* `Tornado <http://www.tornadoweb.org/>`_ >= 2.0;

* `Psycopg <http://initd.org/psycopg/>`_ >= 2.4;

* `gevent <http://www.gevent.org/>`_ >= 1.0;

* `simplejson <https://github.com/simplejson/simplejson>`_ >= 2.1;

* `SQLAlchemy <http://www.sqlalchemy.org/>`_ >= 0.7;

* `libcg <http://libcg.sourceforge.net/>`_;

* `psutil <https://code.google.com/p/psutil/>`_ >= 0.6;

  .. We need 0.6 because of the new memory API (https://code.google.com/p/psutil/wiki/Documentation#Memory).

* `netifaces <http://alastairs-place.net/projects/netifaces/>`_ >= 0.5;

* `PyCrypto <https://www.dlitz.net/software/pycrypto/>`_ >= 2.3;

* `pytz <http://pytz.sourceforge.net/>`_;

* `six <http://pythonhosted.org/six/>`_ >= 1.1;

* `requests <http://docs.python-requests.org/en/latest/>`_ >= 1.0;

* `iso-codes <http://pkg-isocodes.alioth.debian.org/>`_;

* `shared-mime-info <http://freedesktop.org/wiki/Software/shared-mime-info>`_;

* `PyYAML <http://pyyaml.org/wiki/PyYAML>`_ >= 3.10 (only for Importer);

* `BeautifulSoup <http://www.crummy.com/software/BeautifulSoup/>`_ >= 3.2 (only for running tests);

* `mechanize <http://wwwsearch.sourceforge.net/mechanize/>`_ >= 0.2 (only for running tests);

* `coverage <http://nedbatchelder.com/code/coverage/>`_ >= 3.4 (only for running tests);

* `mock <http://www.voidspace.org.uk/python/mock>`_ >= 1.0 (only for running tests);

* `Sphinx <http://sphinx-doc.org/>`_ (only for building documentation).

You will also require a Linux kernel with support for control groups and namespaces. Support has been in the Linux kernel since 2.6.32, and is provided by Ubuntu 12.04 and later. Other distributions, or systems with custom kernels, may not have support enabled. At a minimum, you will need to enable the following Linux kernel options: ``CONFIG_CGROUPS``, ``CONFIG_CGROUP_CPUACCT``, ``CONFIG_MEMCG`` (previously called as ``CONFIG_CGROUP_MEM_RES_CTLR``), ``CONFIG_CPUSETS``, ``CONFIG_PID_NS``, ``CONFIG_IPC_NS``, ``CONFIG_NET_NS``.

Nearly all dependencies (i.e., all except gevent) can be installed automatically on most Linux distributions (gevent itself is provided on some distributions, but we need the development version which isn't generally available as a package). Instructions for manually installing gevent are below.

On Ubuntu 12.04, one will need to run the following script to satisfy all dependencies (except gevent):

.. sourcecode:: bash

    sudo apt-get install build-essential fpc postgresql postgresql-client \
         gettext python2.7 python-setuptools python-tornado python-psycopg2 \
         python-simplejson python-sqlalchemy python-psutil python-netifaces \
         python-crypto python-tz python-six iso-codes shared-mime-info \
         stl-manual python-beautifulsoup python-mechanize python-coverage \
         python-mock cgroup-lite python-requests

    # Optional.
    # sudo apt-get install phppgadmin python-yaml python-sphinx

On Arch Linux, the following command will install almost all dependencies (four of them can be found in the AUR):

.. sourcecode:: bash

    sudo pacman -S base-devel fpc postgresql postgresql-client python2 \
         setuptools python2-tornado python2-psycopg2 python2-simplejson \
         python2-sqlalchemy python2-psutil python2-netifaces python2-crypto \
         python2-pytz python2-six iso-codes shared-mime-info \
         python2-beautifulsoup3 python2-mechanize python2-requests

    # Install gevent from repository.
    sudo pacman -S python2-gevent-beta

    # Install the following from AUR.
    # https://aur.archlinux.org/packages/libcgroup/
    # https://aur.archlinux.org/packages/sgi-stl-doc/
    # https://aur.archlinux.org/packages/python2-coverage/
    # https://aur.archlinux.org/packages/python2-mock/

    # Optional.
    # sudo pacman -S phppgadmin python2-yaml python-sphinx

If you prefer using Python Package Index, you can retrieve all Python dependencies with this line:

.. sourcecode:: bash

    sudo pip install -r REQUIREMENTS.txt

Installing gevent (version 1.0)
===============================

If you don't use Arch Linux, to install gevent please clone its GIT repository and use the ``setup.py`` script:

.. sourcecode:: bash

    git clone git@github.com:surfly/gevent.git
    cd gevent
    python ./setup.py build
    sudo python ./setup.py install


Installing CMS
==============

You can download CMS |release| from :gh_download:`GitHub` and extract it on your filesystem. After that, you can install it (recommended, not necessary though):

.. sourcecode:: bash

    ./setup.py build
    sudo ./setup.py install

If you install CMS, you also need to add your user to the ``cmsuser`` group and logout to make the change effective:

.. sourcecode:: bash

    sudo usermod -a -G cmsuser

You can verify to be in the group by issuing the command:

.. sourcecode:: bash

    groups


.. _installation_updatingcms:

Updating CMS
============

As CMS develops, the database schema it uses to represent its data may be updated and new versions may introduce changes that are incompatible with older versions.

To preserve the data stored on the database you need to dump it on the filesystem using ``cmsContestExporter`` **before you update CMS** (i.e. with the old version).

You can then update CMS and reset the database schema by running:

.. sourcecode:: bash

    cmsDropDB
    cmsInitDB

To load the previous data back into the database you can use ``cmsContestImporter``: it will adapt the data model automatically on-the-fly (you can use ``cmsDumpUpdater`` to store the updated version back on disk and speed up future imports).

