"""autogenerated by genmsg_py from SegStatus.msg. Do not edit."""
import roslib.message
import struct


class SegStatus(roslib.message.Message):
  _md5sum = "537b841aea584803156cc8b3c36d1a6b"
  _type = "look_ahead/SegStatus"
  _has_header = False #flag to mark the presence of a Header object
  _full_text = """#Message that will be sent giving the status of segments issued by the Path Planner
#will be recieved by the Path Planner, the Look Ahead
#will be sent by the Velocity Node

#Requests a new path segment from the Path Planner Node
bool segComplete

#Distance made (Progress made thus far)
float64 progress_made

"""
  __slots__ = ['segComplete','progress_made']
  _slot_types = ['bool','float64']

  def __init__(self, *args, **kwds):
    """
    Constructor. Any message fields that are implicitly/explicitly
    set to None will be assigned a default value. The recommend
    use is keyword arguments as this is more robust to future message
    changes.  You cannot mix in-order arguments and keyword arguments.
    
    The available fields are:
       segComplete,progress_made
    
    @param args: complete set of field values, in .msg order
    @param kwds: use keyword arguments corresponding to message field names
    to set specific fields. 
    """
    if args or kwds:
      super(SegStatus, self).__init__(*args, **kwds)
      #message fields cannot be None, assign default values for those that are
      if self.segComplete is None:
        self.segComplete = False
      if self.progress_made is None:
        self.progress_made = 0.
    else:
      self.segComplete = False
      self.progress_made = 0.

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
      buff.write(_struct_Bd.pack(_x.segComplete, _x.progress_made))
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
      (_x.segComplete, _x.progress_made,) = _struct_Bd.unpack(str[start:end])
      self.segComplete = bool(self.segComplete)
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
      buff.write(_struct_Bd.pack(_x.segComplete, _x.progress_made))
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
      (_x.segComplete, _x.progress_made,) = _struct_Bd.unpack(str[start:end])
      self.segComplete = bool(self.segComplete)
      return self
    except struct.error as e:
      raise roslib.message.DeserializationError(e) #most likely buffer underfill

_struct_I = roslib.message.struct_I
_struct_Bd = struct.Struct("<Bd")
