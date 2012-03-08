"""autogenerated by genmsg_py from Obstacles.msg. Do not edit."""
import roslib.message
import struct


class Obstacles(roslib.message.Message):
  _md5sum = "b27e18c6490e5a2025906af3f6bc6257"
  _type = "alpha_steering/Obstacles"
  _has_header = False #flag to mark the presence of a Header object
  _full_text = """#The message tells whether or not an obstacle exists on current and next path segements and the distance along the path
bool exists		      
float64 distance






		      


		      

"""
  __slots__ = ['exists','distance']
  _slot_types = ['bool','float64']

  def __init__(self, *args, **kwds):
    """
    Constructor. Any message fields that are implicitly/explicitly
    set to None will be assigned a default value. The recommend
    use is keyword arguments as this is more robust to future message
    changes.  You cannot mix in-order arguments and keyword arguments.
    
    The available fields are:
       exists,distance
    
    @param args: complete set of field values, in .msg order
    @param kwds: use keyword arguments corresponding to message field names
    to set specific fields. 
    """
    if args or kwds:
      super(Obstacles, self).__init__(*args, **kwds)
      #message fields cannot be None, assign default values for those that are
      if self.exists is None:
        self.exists = False
      if self.distance is None:
        self.distance = 0.
    else:
      self.exists = False
      self.distance = 0.

  def _get_types(self):
    """
    internal API method
    """
    return self._slot_types

  def serialize(self, buff):
    """
    serialize message into buffer
    @param buff: buffer
    @type  buff: StringIO
    """
    try:
      _x = self
      buff.write(_struct_Bd.pack(_x.exists, _x.distance))
    except struct.error as se: self._check_types(se)
    except TypeError as te: self._check_types(te)

  def deserialize(self, str):
    """
    unpack serialized message in str into this message instance
    @param str: byte array of serialized message
    @type  str: str
    """
    try:
      end = 0
      _x = self
      start = end
      end += 9
      (_x.exists, _x.distance,) = _struct_Bd.unpack(str[start:end])
      self.exists = bool(self.exists)
      return self
    except struct.error as e:
      raise roslib.message.DeserializationError(e) #most likely buffer underfill


  def serialize_numpy(self, buff, numpy):
    """
    serialize message with numpy array types into buffer
    @param buff: buffer
    @type  buff: StringIO
    @param numpy: numpy python module
    @type  numpy module
    """
    try:
      _x = self
      buff.write(_struct_Bd.pack(_x.exists, _x.distance))
    except struct.error as se: self._check_types(se)
    except TypeError as te: self._check_types(te)

  def deserialize_numpy(self, str, numpy):
    """
    unpack serialized message in str into this message instance using numpy for array types
    @param str: byte array of serialized message
    @type  str: str
    @param numpy: numpy python module
    @type  numpy: module
    """
    try:
      end = 0
      _x = self
      start = end
      end += 9
      (_x.exists, _x.distance,) = _struct_Bd.unpack(str[start:end])
      self.exists = bool(self.exists)
      return self
    except struct.error as e:
      raise roslib.message.DeserializationError(e) #most likely buffer underfill

_struct_I = roslib.message.struct_I
_struct_Bd = struct.Struct("<Bd")