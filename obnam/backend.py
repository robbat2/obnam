"""Backup program backend for communicating with the backup server.

This implementation only stores the stuff locally, however.

"""


import logging
import os
import pwd
import stat
import urlparse

import paramiko

import uuid
import obnam.cache
import obnam.cmp
import obnam.map
import obnam.obj


# Block filenames are created using the following scheme:
#
# For each backup run, we create one directory, named by a UUID. Inside
# this directory we create sub-directories, named by sequential integers,
# up to a certain number of levels. The actual block files are created at
# the lowest level, and we create the next lowest level directory when
# we've reached some maximum of files in the directory.
#
# The rationale is that having too many files in one directory makes all
# operations involving that directory slow, in many filesystems, because
# of linear searches. By putting, say, only 256 files per directory, we
# can keep things reasonably fast. However, if we create a a lot of blocks,
# we'll end up creating a lot of directories, too. Thus, several levels of
# directories are needed.
#
# With 256 files per directory, and three levels of directories, and one
# megabyte per block file, we can create 16 terabytes of backup data without
# exceeding contraints. After that, we get more than 256 entries per
# directory, making things slow, but it'll still work.

MAX_BLOCKS_PER_DIR = 256
LEVELS = 3


class BackendData:

    def __init__(self):
        self.config = None
        self.url = None
        self.user = None
        self.host = None
        self.port = None
        self.path = None
        self.cache = None
        self.blockdir = None
        self.dircounts = [0] * LEVELS
        self.sftp_transport = None
        self.sftp_client = None


def get_default_user():
    """Return the username of the current user"""
    if "LOGNAME" in os.environ:
        return os.environ["LOGNAME"]
    else:
        return pwd.getpwuid(os.getuid())[0]


def parse_store_url(url):
    """Parse a store url
    
    The url must either be a plain pathname, or it starts with sftp://
    and specifies a remote store. Return a tuple username, host, port,
    path, where elements can be None if they are meant to be the default
    or are not relevant.
    
    """
    
    # urlparse in Python 2.4 doesn't know, by default, that sftp uses
    # a netloc
    if "sftp" not in urlparse.uses_netloc:
        urlparse.uses_netloc.append("sftp")
    
    user = host = port = path = None
    (scheme, netloc, path, query, fragment) = urlparse.urlsplit(url)
    
    if scheme == "sftp":
        if "@" in netloc:
            (user, netloc) = netloc.split("@", 1)
        if ":" in netloc:
            (host, port) = netloc.split(":", 1)
            port = int(port)
        else:
            host = netloc
    else:
        path = url
    
    return user, host, port, path


def init(config, cache):
    """Initialize the subsystem and return an opaque backend object"""
    be = BackendData()
    be.config = config
    be.url = config.get("backup", "store")
    (be.user, be.host, be.port, be.path) = parse_store_url(be.url)
    if be.user is None:
        be.user = get_default_user()
    if be.port is None:
        be.port = 22 # 22 is the default port for ssh
    be.cache = cache
    be.blockdir = str(uuid.uuid4())
    return be


def increment_dircounts(be):
    """Increment the counter for lowest directory level, and more if need be"""
    level = len(be.dircounts) - 1
    while level >= 0:
        be.dircounts[level] += 1
        if be.dircounts[level] <= MAX_BLOCKS_PER_DIR:
            break
        be.dircounts[level] = 0
        level -= 1


def generate_block_id(be):
    """Generate a new identifier for the block, when stored remotely"""
    increment_dircounts(be)
    id = be.blockdir
    for i in be.dircounts:
        id = os.path.join(id, "%d" % i)
    return id


def _block_remote_pathname(be, block_id):
    """Return pathname on server for a given block id"""
    return os.path.join(be.path, block_id)


def _use_sftp(be):
    """Should we use sftp or local filesystem?"""
    return be.host is not None


def _connect_sftp(be):
    """Connect to the server, unless already connected"""
    if be.sftp_transport is None:
        ssh_key_file = be.config.get("backup", "ssh-key")
        logging.debug("Getting private key from %s" % ssh_key_file)
        pkey = paramiko.DSSKey.from_private_key_file(ssh_key_file)

        logging.debug("Connecting to sftp server: host=%s, port=%d" % 
                        (be.host, be.port))
        be.sftp_transport = paramiko.Transport((be.host, be.port))

        logging.debug("Authenticating as user %s" % be.user)
        be.sftp_transport.connect(username=be.user, pkey=pkey)

        logging.debug("Opening sftp client")
        be.sftp_client = be.sftp_transport.open_sftp_client()


def sftp_makedirs(sftp, dirname, mode=0777):
    """Create dirname, if it doesn't exist, and all its parents, too"""
    stack = []
    while dirname:
        stack.append(dirname)
        dirname2 = os.path.dirname(dirname)
        if dirname2 == dirname:
            dirname = None
        else:
            dirname = dirname2

    while stack:
        dirname, stack = stack[-1], stack[:-1]
        try:
            sftp.lstat(dirname).st_mode
        except IOError:
            exists = False
        else:
            exists = True
        if not exists:
            logging.debug("Creating remote directory %s" % dirname)
            sftp.mkdir(dirname, mode=mode)


def upload(be, block_id, block):
    """Start the upload of a block to the remote server"""
    logging.debug("Uploading block %s (%d bytes)" % (block_id, len(block)))
    if _use_sftp(be):
        _connect_sftp(be)
        pathname = _block_remote_pathname(be, block_id)
        sftp_makedirs(be.sftp_client, os.path.dirname(pathname))
        f = be.sftp_client.file(pathname, "w")
        f.write(block)
        f.close()
    else:
        dir_full = os.path.join(be.path, os.path.dirname(block_id))
        if not os.path.isdir(dir_full):
            os.makedirs(dir_full, 0700)
        f = file(_block_remote_pathname(be, block_id), "w")
        f.write(block)
        f.close()
    return None


def download(be, block_id):
    """Download a block from the remote server
    
    Return exception for error, or None for OK.
    
    """
    
    if _use_sftp(be):
        try:
            _connect_sftp(be)
            f = be.sftp_client.file(_block_remote_pathname(be, block_id), "r")
            block = f.read()
            f.close()
            obnam.cache.put_block(be.cache, block_id, block)
        except IOError, e:
            return e
    else:
        try:
            f = file(_block_remote_pathname(be, block_id), "r")
            block = f.read()
            f.close()
            obnam.cache.put_block(be.cache, block_id, block)
        except IOError, e:
            return e
    return None


def sftp_listdir_abs(sftp, dirname):
    """Like SFTPClient's listdir_attr, but absolute pathnames"""
    items = sftp.listdir_attr(dirname)
    for item in items:
        item.filename = os.path.join(dirname, item.filename)
    return items


def sftp_recursive_listdir(sftp, dirname="."):
    """Similar to SFTPClient's listdir_attr, but recursively"""
    list = []
    unprocessed = listdir_abs(sftp, dirname)
    while unprocessed:
        item, unprocessed = unprocessed[0], unprocessed[1:]
        print item.filename
        if stat.S_ISDIR(item.st_mode):
            unprocessed += listdir_abs(sftp, item.filename)
        list.append(item.filename)
    return list


def list(be):
    """Return list of all files on the remote server"""
    if _use_sftp(be):
        list = sftp_recursive_listdir(be.sftp_client, be.path)
        list = [x.filename for x in list if stat.S_ISDIR(x.st_mode)]
    else:
        list = []
        for dirpath, _, filenames in os.walk(be.path):
            if dirpath.startswith(be.path):
                dirpath = dirpath[len(be.path):]
                if dirpath.startswith(os.sep):
                    dirpath = dirpath[len(os.sep):]
            list += [os.path.join(dirpath, x) for x in filenames]
        return list


def remove(be, block_id):
    """Remove a block from the remote server"""
    pathname = _block_remote_pathname(be, block_id)
    if _use_sftp(be):
        be.sftp_client.remove(pathname)
    else:
        if os.path.exists(pathname):
            os.remove(pathname)