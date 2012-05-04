# ROS Stack Management #

We have been utilizing ROS stacks to manage our individual ROS packages.
We will try to use a single package per node. This will encourage
appropriate message passing between nodes and make sure they are not too
tightly coupled.

Stacks utilize a `stack.xml` file which contains dependencies to be
included for every package. The ROS stack will automatically build all
packages within it's root directory.

Complete documentation can be found at the [ROSWiki][].

  [ROSWiki]: http://www.ros.org/wiki/Stacks