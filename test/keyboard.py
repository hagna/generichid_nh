#!/usr/bin/python2.4
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
# 
# $Id: IOCTL.py 2 2007-06-04 12:27:36Z keith.dart $
#
#    Copyright (C) 1999-2006  Keith Dart <keith@kdart.com>
#
#    This library is free software; you can redistribute it and/or
#    modify it under the terms of the GNU Lesser General Public
#    License as published by the Free Software Foundation; either
#    version 2.1 of the License, or (at your option) any later version.
#
#    This library is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#    Lesser General Public License for more details.

"""
Linux ioctl macros. Taken from /usr/include/asm/ioctl.h

"""
from __future__ import print_function

# ioctl command encoding: 32 bits total, command in lower 16 bits,
# size of the parameter structure in the lower 14 bits of the
# upper 16 bits.
# Encoding the size of the parameter structure in the ioctl request
# is useful for catching programs compiled with old versions
# and to avoid overwriting user space outside the user buffer area.
# The highest 2 bits are reserved for indicating the ``access mode''.
# NOTE: This limits the max parameter size to 16kB -1 !
#
#
# The following is for compatibility across the various Linux
# platforms.  The i386 ioctl numbering scheme doesn't really enforce
# a type field.  De facto, however, the top 8 bits of the lower 16
# bits are indeed used as a type field, so we might just as well make
# this explicit here.  Please be sure to use the decoding macros
# below from now on.

import struct
sizeof = struct.calcsize

_IOC_NRBITS = 8
_IOC_TYPEBITS = 8
_IOC_SIZEBITS = 14
_IOC_DIRBITS = 2
_IOC_NRMASK = ((1 << _IOC_NRBITS)-1)
_IOC_TYPEMASK = ((1 << _IOC_TYPEBITS)-1)
_IOC_SIZEMASK = ((1 << _IOC_SIZEBITS)-1)
_IOC_DIRMASK = ((1 << _IOC_DIRBITS)-1)
_IOC_NRSHIFT = 0
_IOC_TYPESHIFT = (_IOC_NRSHIFT+_IOC_NRBITS)
_IOC_SIZESHIFT = (_IOC_TYPESHIFT+_IOC_TYPEBITS)
_IOC_DIRSHIFT = (_IOC_SIZESHIFT+_IOC_SIZEBITS)

IOCSIZE_MASK = (_IOC_SIZEMASK << _IOC_SIZESHIFT)
IOCSIZE_SHIFT = (_IOC_SIZESHIFT)

### 
# direction bits
_IOC_NONE = 0
_IOC_WRITE = 1
_IOC_READ = 2

def _IOC(dir,type,nr,FMT):
        return int((((dir)  << _IOC_DIRSHIFT) | \
         ((type) << _IOC_TYPESHIFT) | \
         ((nr)   << _IOC_NRSHIFT) | \
         ((FMT) << _IOC_SIZESHIFT)) & 0xffffffff )


# used to create numbers
# type is the assigned type from the kernel developers
# nr is the base ioctl number (defined by driver writer)
# FMT is a struct module format string.
def _IO(type,nr): return _IOC(_IOC_NONE,(type),(nr),0)
def _IOR(type,nr,FMT): return _IOC(_IOC_READ,(type),(nr),sizeof(FMT))
def _IOW(type,nr,FMT): return _IOC(_IOC_WRITE,(type),(nr),sizeof(FMT))
def _IOWR(type,nr,FMT): return _IOC(_IOC_READ|_IOC_WRITE,(type),(nr),sizeof(FMT))

# used to decode ioctl numbers
def _IOC_DIR(nr): return (((nr) >> _IOC_DIRSHIFT) & _IOC_DIRMASK)
def _IOC_TYPE(nr): return (((nr) >> _IOC_TYPESHIFT) & _IOC_TYPEMASK)
def _IOC_NR(nr): return (((nr) >> _IOC_NRSHIFT) & _IOC_NRMASK)
def _IOC_SIZE(nr): return (((nr) >> _IOC_SIZESHIFT) & _IOC_SIZEMASK)

"""
Only truly useful and general functions should go here. Also, things that
fix Python's "warts" can go here. Many of these would be useful as new
builtins. ;-)

"""



import sys
from math import ceil
from errno import EINTR
from collections import deque, Callable
import functools

# python 3 compatibility
try:
    long
except NameError: # signals python3
    #import builtins as __builtins__
    long = int
    _biname = "builtins"

    def callable(f):
        return isinstance(f, Callable)

    def execfile(fn, glbl=None, loc=None):
        glbl = glbl or globals()
        loc = loc or locals()
        exec(open(fn).read(), glbl, loc)
else: # python 2
    _biname = "__builtin__"
    execfile = execfile
    callable = callable


# partial function returns callable with some parameters already setup to run. 
partial = functools.partial

# Works like None, but is also a no-op callable and empty iterable.
class NULLType(type):
    def __new__(cls, name, bases, dct):
        return type.__new__(cls, name, bases, dct)
    def __init__(cls, name, bases, dct):
        super(NULLType, cls).__init__(name, bases, dct)
    def __str__(self):
        return ""
    def __repr__(self):
        return "NULL"
    def __nonzero__(self):
        return False
    def __len__(self):
        return 0
    def __call__(self, *args, **kwargs):
        return None
    def __contains__(self, item):
        return False
    def __iter__(self):
        return self
    def next(*args):
        raise StopIteration
NULL = NULLType("NULL", (type,), {})

# shortcuts to save time
sow = sys.stdout.write
sew = sys.stderr.write
# the embedded vim interpreter replaces stdio with objects that don't have a
# flush method!
try: 
    soflush = sys.stdout.flush
except AttributeError:
    soflush = NULL
try:
    seflush = sys.stderr.flush
except AttributeError:
    seflush = NULL

class Enum(int):
    def __new__(cls, val, name=None): # name must be optional for unpickling to work
        v = int.__new__(cls, val)
        v._name = str(name)
        return v
    def __getstate__(self):
        return int(self), self._name
    def __setstate__(self, args):
        i, self._name = args
    def __str__(self):
        return self._name
    def __repr__(self):
        return "%s(%d, %r)" % (self.__class__.__name__, self, self._name)

class Enums(list):
    def __init__(self, *init, **kwinit):
        for i, val in enumerate(init):
            if issubclass(type(val), list):
                for j, subval in enumerate(val):
                    self.append(Enum(i+j, str(subval)))
            elif isinstance(val, Enum):
                self.append(val)
            else:
                self.append(Enum(i, str(val)))
        for name, value in kwinit.items():
            enum = Enum(int(value), name)
            self.append(enum)
        self._mapping = None
        self.sort()

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, list.__repr__(self))

    # works nicely with WWW framework.
    choices = property(lambda s: map(lambda e: (int(e), str(e)), s))

    def find(self, value):
        if type(value) is str:
            return self.findstring(value)
        else:
            i = self.index(int(value))
            return self[i]

    def get_mapping(self):
        if self._mapping is None:
            d = dict(map(lambda it: (str(it), it), self))
            self._mapping = d
            return d
        else:
            return self._mapping

    def findstring(self, string):
        """Returns the Enum object given a name string."""
        d = self.get_mapping()
        try:
            return d[string]
        except KeyError:
            raise ValueError("Enum string not found.")

# common enumerations
NO = Enum(0, "NO")
YES = Enum(1, "YES")
DEFAULT = Enum(2, "DEFAULT")
UNKNOWN = Enum(3, "UNKNOWN")

# emulate an unsigned 32 bit and 64 bit ints with a long
class unsigned(long):
    floor = 0
    ceiling = 4294967295
    bits = 32
    _mask = 0xFFFFFFFF
    def __new__(cls, val):
        return long.__new__(cls, val)
    def __init__(self, val):
        if val < self.floor or val > self.ceiling:
            raise OverflowError("value %s out of range for type %s" % (val, self.__class__.__name__))
    def __repr__(self):
        return "%s(%sL)" % (self.__class__.__name__, self)
    def __add__(self, other):
        return self.__class__(long.__add__(self, other))
    def __sub__(self, other):
        return self.__class__(long.__sub__(self, other))
    def __mul__(self, other):
        return self.__class__(long.__mul__(self, other))
    def __floordiv__(self, other):
        return self.__class__(long.__floordiv__(self, other))
    def __mod__(self, other):
        return self.__class__(long.__mod__(self, other))
    def __divmod__(self, other):
        return self.__class__(long.__divmod__(self, other))
    def __pow__(self, other, modulo=None):
        return self.__class__(long.__pow__(self, other, modulo))
    def __lshift__(self, other):
        return self.__class__(long.__lshift__(self, other) & self._mask)
    def __rshift__(self, other):
        return self.__class__(long.__rshift__(self, other))
    def __and__(self, other):
        return self.__class__(long.__and__(self, other))
    def __xor__(self, other):
        return self.__class__(long.__xor__(self, other))
    def __or__(self, other):
        return self.__class__(long.__or__(self, other))
    def __div__(self, other):
        return self.__class__(long.__div__(self, other))
    def __truediv__(self, other):
        return self.__class__(long.__truediv__(self, other))
    def __neg__(self):
        return self.__class__(long.__neg__(self))
    def __pos__(self):
        return self.__class__(long.__pos__(self))
    def __abs__(self):
        return self.__class__(long.__abs__(self))
    def __invert__(self):
        return self.__class__(long.__invert__(self))
    def __radd__(self, other):
        return self.__class__(long.__radd__(self, other))
    def __rand__(self, other):
        return self.__class__(long.__rand__(self, other))
    def __rdiv__(self, other):
        return self.__class__(long.__rdiv__(self, other))
    def __rdivmod__(self, other):
        return self.__class__(long.__rdivmod__(self, other))
    def __rfloordiv__(self, other):
        return self.__class__(long.__rfloordiv__(self, other))
    def __rlshift__(self, other):
        return self.__class__(long.__rlshift__(self, other))
    def __rmod__(self, other):
        return self.__class__(long.__rmod__(self, other))
    def __rmul__(self, other):
        return self.__class__(long.__rmul__(self, other))
    def __ror__(self, other):
        return self.__class__(long.__ror__(self, other))
    def __rpow__(self, other):
        return self.__class__(long.__rpow__(self, other))
    def __rrshift__(self, other):
        return self.__class__(long.__rrshift__(self, other))
    def __rshift__(self, other):
        return self.__class__(long.__rshift__(self, other))
    def __rsub__(self, other):
        return self.__class__(long.__rsub__(self, other))
    def __rtruediv__(self, other):
        return self.__class__(long.__rtruediv__(self, other))
    def __rxor__(self, other):
        return self.__class__(long.__rxor__(self, other))


class unsigned64(unsigned):
    floor = 0
    ceiling = 18446744073709551615
    bits = 64
    _mask = 0xFFFFFFFFFFFFFFFF

# a list that self-maintains a sorted order
class sortedlist(list):
    def insort(self, x):
        hi = len(self)
        lo = 0
        while lo < hi:
            mid = (lo+hi)//2
            if x < self[mid]:
               hi = mid
            else:
               lo = mid+1
        self.insert(lo, x)
    append = insort

# print helpers
def _printobj(obj):
    sow(str(obj))
    sow(" ")

def _printerr(obj):
    sew(str(obj))
    sew(" ")

def Write(*args):
    map (_printobj, args)
    soflush()

def Print(*args):
    """Print is a replacement for the built-in print statement. Except that it
    is a function object.  """
    map (_printobj, args)
    sow("\n")
    soflush()

def Printerr(*args):
    """Printerr writes to stderr."""
    map(_printerr, args)
    sew("\n")
    seflush()

def IF(test, tv, fv=None):
    """Functional 'if' test. Deprecated, use new Python conditional instead."""
    if test:
        return tv
    else:
        return fv

def sgn(val):
    """Sign function. Returns -1 if val negative, 0 if zero, and 1 if
    positive.
    """
    try:
        return val._sgn_()
    except AttributeError:
        if val == 0:
            return 0
        if val > 0:
            return 1
        else:
            return -1

# Nice floating point range function from Python snippets
def frange(limit1, limit2=None, increment=1.0):
  """
  Range function that accepts floats (and integers).

  Usage:
  frange(-2, 2, 0.1)
  frange(10)
  frange(10, increment=0.5)

  The returned value is an iterator.  Use list(frange(...)) for a list.
  """
  if limit2 is None:
    limit2, limit1 = limit1, 0.
  else:
    limit1 = float(limit1)
  count = int(ceil((limit2 - limit1)/increment))
  return (limit1 + n*increment for n in xrange(0, count))

class Queue(deque):
    def push(self, obj):
        self.appendleft(obj)

class Stack(deque):
    def push(self, obj):
        self.append(obj)

# a self-substituting string object. Just set attribute names to mapping names
# that are given in the initializer string.
class mapstr(str):
    def __new__(cls, initstr, **kwargs):
        s = str.__new__(cls, initstr)
        return s
    def __init__(self, initstr, **kwargs):
        d = {}
        for name in _findkeys(self):
            d[name] = kwargs.get(name, None)
        self.__dict__["_attribs"] = d
    def __setattr__(self, name, val):
        if name not in self.__dict__["_attribs"].keys():
            raise AttributeError("invalid attribute name %r" % (name,))
        self.__dict__["_attribs"][name] = val
    def __getattr__(self, name):
        try:
            return self.__dict__["_attribs"][name]
        except KeyError:
            raise AttributeError("Invalid attribute %r" % (name,))
    def __str__(self):
        if None in self._attribs.values():
            raise ValueError("one of the attributes %r is not set" % (self._attribs.keys(),))
        return self % self._attribs
    def __call__(self, **kwargs):
        for name, value in kwargs.items():
            setattr(self, name, value)
        return self % self._attribs
    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, str.__repr__(self))
    @property
    def attributes(self):
        return self._attribs.keys()

import re
_findkeys = re.compile(r"%\((\w+)\)").findall
_findfkeys = re.compile(r"[^{]{(\w+)}").findall
del re

# a string with format-style substitutions (limited to the form {name})
# with attribute style setters, and inspection of defined substitutions
# (attributes)
class formatstr(str):
    def __new__(cls, initstr, **kwargs):
        s = str.__new__(cls, initstr)
        return s

    def __init__(self, initstr, **kwargs):
        d = {}
        for name in _findfkeys(self):
            d[name] = kwargs.get(name, None)
        self.__dict__["_attribs"] = d

    def __setattr__(self, name, val):
        if name not in self.__dict__["_attribs"].keys():
            raise AttributeError("invalid attribute name %r" % (name,))
        self.__dict__["_attribs"][name] = val

    def __getattr__(self, name):
        try:
            return self.__dict__["_attribs"][name]
        except KeyError:
            raise AttributeError("Invalid attribute %r" % (name,))

    def __str__(self):
        if None in self._attribs.values():
            raise ValueError("one of the attributes %r is not set" % (self._attribs.keys(),))
        return self.format(**self._attribs)

    def __call__(self, **kwargs):
        for name, value in kwargs.items():
            self.__setattr__(name, value)
        return self.format(**self._attribs)

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, str.__repr__(self))

    @property
    def attributes(self):
        return self._attribs.keys()


# metaclasses... returns a new class with given bases and class attributes
def newclass(name, *bases, **attribs):
    class _NewType(type):
        def __new__(cls):
            return type.__new__(cls, str(name), bases, attribs)
        def __init__(self, *args, **kwargs):
            pass # XXX quick fix for python 2.6, not sure if this is correct. seems to work.
    return _NewType()


# decorator for making methods enter the debugger on an exception
def debugmethod(meth):
    def _lambda(*iargs, **ikwargs):
        try:
            return meth(*iargs, **ikwargs)
        except:
            ex, val, tb = sys.exc_info()
            from pycopia import debugger
            debugger.post_mortem(tb, ex, val)
    return _lambda

# decorator to make system call methods safe from EINTR
def systemcall(meth):
    # have to import this way to avoid a circular import
    from _socket import error as SocketError
    def systemcallmeth(*args, **kwargs):
        while 1:
            try:
                rv = meth(*args, **kwargs)
            except EnvironmentError as why:
                if why.args and why.args[0] == EINTR:
                    continue
                else:
                    raise
            except SocketError as why:
                if why.args and why.args[0] == EINTR:
                    continue
                else:
                    raise
            else:
                break
        return rv
    return systemcallmeth


def removedups(s):
    """Return a list of the elements in s, but without duplicates.
Thanks to Tim Peters for fast method.
    """
    n = len(s)
    if n == 0:
        return []
    u = {}
    try:
        for x in s:
            u[x] = 1
    except TypeError:
        del u  # move on to the next method
    else:
        return u.keys()
    # We can't hash all the elements.  Second fastest is to sort,
    # which brings the equal elements together; then duplicates are
    # easy to weed out in a single pass.
    try:
        t = list(s)
        t.sort()
    except TypeError:
        del t  # move on to the next method
    else:
        assert n > 0
        last = t[0]
        lasti = i = 1
        while i < n:
            if t[i] != last:
                t[lasti] = last = t[i]
                lasti = lasti + 1
            i = i + 1
        return t[:lasti]
    # Brute force is all that's left.
    u = []
    for x in s:
        if x not in u:
            u.append(x)
    return u


def pprint_list(clist, indent=0, width=74):
    """pprint_list(thelist, [indent, [width]])
Prints the elements of a list to the screen fitting the most elements
per line.  Should not break an element across lines. Sort of like word
wrap for lists."""
    indent = min(max(indent,0),width-1)
    if indent:
        print (" " * indent, end="")
    print ("[", end="")
    col = indent + 2
    for c in clist[:-1]:
        ps = "%r," % (c)
        col = col + len(ps) + 1
        if col > width:
            print()
            col = indent + len(ps) + 1
            if indent:
                print (" " * indent, end="")
        print (ps, end="")
    if col + len(clist[-1]) > width:
        print()
        if indent:
            print (" " * indent, end="")
    print ("%r ]" % (clist[-1],))

def reorder(datalist, indexlist):
    """reorder(datalist, indexlist)
    Returns a new list that is ordered according to the indexes in the
    indexlist.  
    e.g.
    reorder(["a", "b", "c"], [2, 0, 1]) -> ["c", "a", "b"]
    """
    return [datalist[idx] for idx in indexlist]

def enumerate(collection):
    'Generates an indexed series:  (0,coll[0]), (1,coll[1]) ...'
    i = 0
    it = iter(collection)
    while 1:
        yield (i, it.next())
        i += 1

def flatten(alist):
    rv = []
    for val in alist:
        if isinstance(val, list):
            rv.extend(flatten(val))
        else:
            rv.append(val)
    return rv

def str2hex(s):
    res = ["'"]
    for c in s:
        res.append("\\x%02x" % ord(c))
    res.append("'")
    return "".join(res)

def hexdigest(s):
    return "".join(["%02x" % ord(c) for c in s])

def unhexdigest(s):
    l = []
    for i in xrange(0, len(s), 2):
        l.append(chr(int(s[i:i+2], 16)))
    return "".join(l)

def Import(modname):
    try:
        return sys.modules[modname]
    except KeyError:
        pass
    mod = __import__(modname)
    pathparts = modname.split(".")
    for part in pathparts[1:]:
        mod = getattr(mod, part)
    sys.modules[modname] = mod
    return mod

def add2builtin(name, obj):
    """Add an object to the builtins namespace."""
    bim = sys.modules[_biname]
    if not hasattr(bim, name):
        setattr(bim, name, obj)

def add_exception(excclass, name=None):
    """Add an exception to the builtins namespace."""
    name = name or excclass.__name__
    bimod = sys.modules[_biname]
    if not hasattr(bimod, name):
        setattr(bimod, name, excclass)

"""
Interface to /dev/input/eventX devices. This module provides base classes and
constant values for accessing the Linux input interface. This includes
keyboard, mouse, joystick, and a general event interface.

"""

import sys, os, struct, time, fcntl



INT = "i"
INT2 = "ii"
INT5 = "iiiii"
SHORT = "h"
USHORT = "H"
SHORT4 = "hhhh"

SIZEOF_INT2 = struct.calcsize(INT2)

# Initialize the ioctl constants

# taken from /usr/include/linux/input.h

EVIOCGVERSION   = _IOR(69, 0x01, INT)           # get driver version */
EVIOCGID        = _IOR(69, 0x02, SHORT4)        # get device ID */
EVIOCGREP       = _IOR(69, 0x03, INT2)          # get repeat settings */
EVIOCSREP       = _IOW(69, 0x03, INT2)          # set repeat settings */
EVIOCGKEYCODE   = _IOR(69, 0x04, INT2)          # get keycode */
EVIOCSKEYCODE   = _IOW(69, 0x04, INT2)          # set keycode */
EVIOCGKEY       = _IOR(69, 0x05, INT2)          # get key value */
EVIOCGNAME      = _IOC(_IOC_READ, 69, 0x06, 255)# get device name */
EVIOCGPHYS      = _IOC(_IOC_READ, 69, 0x07, 255)# get physical location */
EVIOCGUNIQ      = _IOC(_IOC_READ, 69, 0x08, 255)# get unique identifier */
EVIOCRMFF       = _IOW(69, 0x81, INT)           # Erase a force effect */
EVIOCSGAIN      = _IOW(69, 0x82, USHORT)        # Set overall gain */
EVIOCSAUTOCENTER= _IOW(69, 0x83, USHORT)        # Enable or disable auto-centering */
EVIOCGEFFECTS   = _IOR(69, 0x84, INT)           # Report number of effects playable at the same time */
EVIOCGRAB       = _IOW(69, 0x90, INT)          # Grab/Release device */

# these take parameters.
def EVIOCGBIT(evtype, len=255):
    return _IOC(_IOC_READ, 69, 0x20 + evtype, len)  # get event bits */

def EVIOCGABS(abs):
    return _IOR(69, 0x40 + abs, INT5)       # get abs value/limits */

def EVIOCGSW(len):
    return _IOC(_IOC_READ, 69, 0x1b, len)   # get all switch states */

def EVIOCGLED(len):
    return _IOC(_IOC_READ, 69, 0x19, len)   #  get all LEDs */

#struct input_event {
#        struct timeval time; = {long seconds, long microseconds}
#        unsigned short type;
#        unsigned short code;
#        unsigned int value;
#};

EVFMT = "llHHi"
EVsize = struct.calcsize(EVFMT)

EV_SYN = 0x00
EV_KEY = 0x01
EV_REL = 0x02
EV_ABS = 0x03
EV_MSC = 0x04
EV_SW = 0x05
EV_LED = 0x11
EV_SND = 0x12
EV_REP = 0x14
EV_FF = 0x15
EV_PWR = 0x16
EV_FF_STATUS = 0x17
EV_MAX = 0x1f

class Features(object):
    """Contains a set of base features. May be actual set as returned by a
    feature request, or a desired set to find.
    """
    NAMES = {
        EV_SYN: "Sync",
        EV_KEY: "Keys or Buttons",
        EV_REL: "Relative Axes",
        EV_ABS: "Absolute Axes",
        EV_MSC: "Miscellaneous",
        EV_SW: "Switches",
        EV_LED: "Leds",
        EV_SND: "Sound",
        EV_REP: "Repeat",
        EV_FF: "Force Feedback",
        EV_PWR: "Power Management",
        EV_FF_STATUS: "Force Feedback Status",
    }

    def __init__(self, bits=0):
        self._bits = bits

    def has_keys(self):
        return (self._bits >> EV_KEY) & 1

    def has_leds(self):
        return (self._bits >> EV_LED) & 1

    def has_sound(self):
        return (self._bits >> EV_SND) & 1

    def has_relative_axes(self):
        return (self._bits >> EV_REL) & 1

    def has_absolute_axes(self):
        return (self._bits >> EV_ABS) & 1

    def has_misc(self):
        return (self._bits >> EV_MSC) & 1

    def has_switches(self):
        return (self._bits >> EV_SW) & 1

    def has_repeat(self):
        return (self._bits >> EV_REP) & 1

    def has_forcefeedback(self):
        return (self._bits >> EV_FF) & 1

    def has_forcefeedback_status(self):
        return (self._bits >> EV_FF_STATUS) & 1

    def has_power(self):
        return (self._bits >> EV_PWR) & 1

    def _make_set(self):
        featureset = set()
        bits = self._bits
        for bit in (EV_KEY, EV_REL, EV_ABS, EV_MSC, EV_SW, EV_LED, EV_SND, EV_REP, EV_FF, EV_PWR, EV_FF_STATUS):
            if (bits >> bit) & 1:
                featureset.add(bit)
        return featureset

    def match(self, other):
        pass #XXX

    def __str__(self):
        s = []
        bits = self._bits
        for bit, name in self.NAMES.items():
            if (bits >> bit) & 1:
                s.append(name)
        return ", ".join(s)


class Event(object):
    """This structure is the collection of data for the general event
    interface. You can create one to write to an event device. If you read from
    the event device using a subclass of the EventDevice object you will get one of these.
    """
    def __init__(self, time=0.0, evtype=0, code=0, value=0):
        self.time = time # timestamp of the event in Unix time.
        self.evtype = evtype # even type (one of EV_* constants)
        self.code = code     # a code related to the event type
        self.value = value   # custom data - meaning depends on type above

    def __str__(self):
        return "Event:\n   time: %f\n evtype: 0x%x\n   code: 0x%x\n  value: 0x%x\n" % \
                    (self.time, self.evtype, self.code, self.value)

    def encode(self):
        tv_sec, tv_usec = divmod(self.time, 1.0)
        return struct.pack(EVFMT, long(tv_sec), long(tv_usec*1000000.0), self.evtype, self.code, self.value)

    def decode(self, ev):
        tv_sec, tv_usec, self.evtype, self.code, self.value = struct.unpack(EVFMT, ev)
        self.time = float(tv_sec) + float(tv_usec)/1000000.0

    def set(self, evtype, code, value):
        self.time = time.time()
        self.evtype = int(evtype)
        self.code = int(code)
        self.value = int(value)


class EventFile(object):
    """Read from a file containing raw recorded events."""
    def __init__(self, fname, mode="r"):
        self._fo = open(fname, mode)
        self._eventq = Queue()

    def read(self, amt=None): # amt not used, provided for compatibility.
        """Read a single Event object from stream."""
        if not self._eventq:
            if not self._fill():
                return None
        return self._eventq.pop()

    def readall(self):
        ev = self.read()
        while ev:
            yield ev
            ev = self.read()

    def _fill(self):
        raw = self._fo.read(EVsize * 32)
        if raw:
            for i in xrange(len(raw)/EVsize):
                ev = Event()
                ev.decode(raw[i*EVsize:(i+1)*EVsize])
                self._eventq.push(ev)
            return True
        else:
            return False


# base class for event devices. Subclass this for your specific device. 
class EventDevice(object):
    DEVNAME = None # must match name string of device 
    def __init__(self, fname=None):
        self._fd = None
        self.name = ""
        self._eventq = Queue()
        self.idbus = self.idvendor = self.idproduct = self.idversion = None
        if fname:
            self.open(fname)
        self.initialize()

    def __str__(self):
        if self.idbus is None:
            self.get_deviceid()
        return "%s: bus=0x%x, vendor=0x%x, product=0x%x, version=0x%x\n   %s" % \
            (self.name, self.idbus, self.idvendor, self.idproduct, self.idversion, self.get_features())

    def _fill(self):
        global EVsize
        try:
            raw = os.read(self._fd, EVsize * 32)
        except EOFError:
            self.close()
        else:
            if raw:
                for i in range(len(raw)/EVsize):
                    ev = Event()
                    ev.decode(raw[i*EVsize:(i+1)*EVsize])
                    self._eventq.push(ev)

    def find(self, start=0, name=None):
        name = name or self.DEVNAME
        assert name is not None, "EventDevice: no name to find"
        for d in range(start, 16):
            filename = "/dev/input/event%d" % (d,)
            if os.path.exists(filename):
                try:
                    self.open(filename)
                except (OSError, IOError): # probably no permissions
                    pass
                else:
                    if name in self.name:
                        return
        self.close()
        raise IOError("Input device %r not found." % (name,))

    def open(self, filename):
        self._fd = os.open(filename, os.O_RDWR)
        name = fcntl.ioctl(self._fd, EVIOCGNAME, chr(0) * 256)
        self.name = name.replace(chr(0), '')

    def fileno(self):
        return self._fd

    def close(self):
        if self._fd is not None:
            os.close(self._fd)
            self._fd = None
            self.name = ""

    def read(self):
        if not self._eventq:
            self._fill()
        return self._eventq.pop()

    def readall(self):
        ev = self.read()
        while ev:
            yield ev
            ev = self.read()

    def write(self, evtype, code, value):
        ev = Event(0.0, evtype, code, value)
        return os.write(self._fd, ev.encode())

    def get_driverversion(self):
        ver = fcntl.ioctl(self._fd, EVIOCGVERSION, '\x00\x00\x00\x00')
        return struct.unpack(INT, ver)[0]

    def get_deviceid(self):
        ver = fcntl.ioctl(self._fd, EVIOCGID, '\x00\x00\x00\x00\x00\x00\x00\x00')
        self.idbus, self.idvendor, self.idproduct, self.idversion = struct.unpack(SHORT4, ver)
        return self.idbus, self.idvendor, self.idproduct, self.idversion

    def get_features(self):
        caps = fcntl.ioctl(self._fd, EVIOCGBIT(0), '\x00\x00\x00\x00')
        caps = struct.unpack(INT, caps)[0]
        return Features(caps)

    def readable(self):
        return bool(self._fd)

    def writable(self):
        return False

    def priority(self):
        return False

    def read_handler(self):
        self._fill()

    def write_handler(self):
        pass

    def pri_handler(self):
        pass

    def hangup_handler(self):
        pass

    def initialize(self):
        pass


def get_device_names(start=0):
    """Returns a list of tuples containing (index, devicename).
    """
    names = []
    for d in range(start, 16):
        filename = "/dev/input/event%d" % (d,)
        if os.path.exists(filename):
            try:
                    fd = os.open(filename, os.O_RDWR)
                    try:
                        name = fcntl.ioctl(fd, EVIOCGNAME, chr(0) * 256)
                    finally:
                        os.close(fd)
                    name = name.replace(chr(0), '')
            except (OSError, IOError): # probably no permissions
                continue
            else:
                names.append((d, name))
    return names


def get_devices(start=0):
    devs = []
    for d in range(start, 16):
        filename = "/dev/input/event%d" % (d,)
        if os.path.exists(filename):
            devs.append(EventDevice(filename))
    return devs


import gobject

import sys
import dbus
import dbus.service
import dbus.mainloop.glib
import time


class Demo(object):
    
    
    def __init__(self, hid, hidinput):
        self.hid = hid
        self.hidinput = hidinput

        self.hid.connect_to_signal("IncomingConnection",
                                    lambda : self.connectionMade("IncomingConnection"))
        self.hid.connect_to_signal("DeviceReleased",
                                    lambda : self.connectionLost("DeviceReleased"))
        self.hidinput.connect_to_signal("Reconnected", 
                                        lambda : self.connectionMade("Reconnected"))
        self.hidinput.connect_to_signal("Disconnected",
                                        lambda : self.connectionLost("Disconnected"))


    def sendKey(self, a, b, c):
        print( "sendKey %r %r %r" % (a, b, c))
        self.hidinput.SendEvent(dbus.Byte(a), dbus.UInt16(b), dbus.Byte(c))


    def connectionMade(self, reason):
        print( "connectionMade %r" % reason)
        #v = self.hidinput.GetProperties()
        #print "Properties are %r" % v


    def connectionLost(self, reason):
        print( "connectionLost %r" % reason)



def main(argv):
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

    bus = dbus.SystemBus()
    
    manager = dbus.Interface(bus.get_object("org.bluez", "/"),
                            "org.bluez.Manager")
    
    # export BTADAPTER=`dbus-send --system --dest=org.bluez --print-reply / org.bluez.Manager.DefaultAdapter | tail -1 | sed 's/^.*"\(.*\)".*$/\1/'`
    path = manager.DefaultAdapter()

    # dbus-send --system --dest=org.bluez --print-reply $BTADAPTER org.freedesktop.DBus.Introspectable.Introspect

    adapter = dbus.Interface(bus.get_object("org.bluez", path), "org.bluez.GenericHID")

    adapter.Activate()
    print( "Acitvated keyboard device class")

    in_device = dbus.Interface(bus.get_object("org.bluez","/org/bluez/input/hci0/device1"),"org.bluez.GenericHIDInput")


    d = Demo(adapter, in_device)
    devices = get_devices()
    for i, dev in enumerate(devices):
        print("%d %s" % (i, dev))

    print("\n")
    i = raw_input("which device do you want to try? [0]")
    if not i:
        i = 0
    i = int(i)
    e = devices[i]
    while 1:
        try:
            for i in e.readall():
                print("%d %d %d" % (i.evtype, i.code, i.value))
                d.sendKey(i.evtype, i.code, i.value)

        except Exception, t:
            print(str(t))
    adapter.Deactivate()
    print( "Deactivated keyboard device class")


if __name__ == '__main__':
    main(sys.argv)


