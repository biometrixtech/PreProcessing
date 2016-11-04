# This file was automatically generated by SWIG (http://www.swig.org).
# Version 2.0.4
#
# Do not make changes to this file unless you know what you are doing--modify
# the SWIG interface file instead.



from sys import version_info
if version_info >= (2,6,0):
    def swig_import_helper():
        from os.path import dirname
        import imp
        fp = None
        try:
            fp, pathname, description = imp.find_module('_dia', [dirname(__file__)])
        except ImportError:
            import _dia
            return _dia
        if fp is not None:
            try:
                _mod = imp.load_module('_dia', fp, pathname, description)
            finally:
                fp.close()
            return _mod
    _dia = swig_import_helper()
    del swig_import_helper
else:
    import _dia
del version_info
try:
    _swig_property = property
except NameError:
    pass # Python < 2.2 doesn't have 'property'.
def _swig_setattr_nondynamic(self,class_type,name,value,static=1):
    if (name == "thisown"): return self.this.own(value)
    if (name == "this"):
        if type(value).__name__ == 'SwigPyObject':
            self.__dict__[name] = value
            return
    method = class_type.__swig_setmethods__.get(name,None)
    if method: return method(self,value)
    if (not static):
        self.__dict__[name] = value
    else:
        raise AttributeError("You cannot add attributes to %s" % self)

def _swig_setattr(self,class_type,name,value):
    return _swig_setattr_nondynamic(self,class_type,name,value,0)

def _swig_getattr(self,class_type,name):
    if (name == "thisown"): return self.this.own()
    method = class_type.__swig_getmethods__.get(name,None)
    if method: return method(self)
    raise AttributeError(name)

def _swig_repr(self):
    try: strthis = "proxy of " + self.this.__repr__()
    except: strthis = ""
    return "<%s.%s; %s >" % (self.__class__.__module__, self.__class__.__name__, strthis,)

try:
    _object = object
    _newclass = 1
except AttributeError:
    class _object : pass
    _newclass = 0


# This file is compatible with both classic and new-style classes.


def dia_matvec(*args):
  """
    dia_matvec(int n_row, int n_col, int n_diags, int L, int offsets, 
        signed char diags, signed char Xx, signed char Yx)
    dia_matvec(int n_row, int n_col, int n_diags, int L, int offsets, 
        unsigned char diags, unsigned char Xx, unsigned char Yx)
    dia_matvec(int n_row, int n_col, int n_diags, int L, int offsets, 
        short diags, short Xx, short Yx)
    dia_matvec(int n_row, int n_col, int n_diags, int L, int offsets, 
        unsigned short diags, unsigned short Xx, 
        unsigned short Yx)
    dia_matvec(int n_row, int n_col, int n_diags, int L, int offsets, 
        int diags, int Xx, int Yx)
    dia_matvec(int n_row, int n_col, int n_diags, int L, int offsets, 
        unsigned int diags, unsigned int Xx, unsigned int Yx)
    dia_matvec(int n_row, int n_col, int n_diags, int L, int offsets, 
        long long diags, long long Xx, long long Yx)
    dia_matvec(int n_row, int n_col, int n_diags, int L, int offsets, 
        unsigned long long diags, unsigned long long Xx, 
        unsigned long long Yx)
    dia_matvec(int n_row, int n_col, int n_diags, int L, int offsets, 
        float diags, float Xx, float Yx)
    dia_matvec(int n_row, int n_col, int n_diags, int L, int offsets, 
        double diags, double Xx, double Yx)
    dia_matvec(int n_row, int n_col, int n_diags, int L, int offsets, 
        long double diags, long double Xx, long double Yx)
    dia_matvec(int n_row, int n_col, int n_diags, int L, int offsets, 
        npy_cfloat_wrapper diags, npy_cfloat_wrapper Xx, 
        npy_cfloat_wrapper Yx)
    dia_matvec(int n_row, int n_col, int n_diags, int L, int offsets, 
        npy_cdouble_wrapper diags, npy_cdouble_wrapper Xx, 
        npy_cdouble_wrapper Yx)
    dia_matvec(int n_row, int n_col, int n_diags, int L, int offsets, 
        npy_clongdouble_wrapper diags, npy_clongdouble_wrapper Xx, 
        npy_clongdouble_wrapper Yx)
    """
  return _dia.dia_matvec(*args)

