# coding=utf-8
# =============================================================================
# Copyright (c) 2025 FLIR Integrated Imaging Solutions, Inc. All Rights Reserved.
#
# This software is the confidential and proprietary information of FLIR
# Integrated Imaging Solutions, Inc. ("Confidential Information"). You
# shall not disclose such Confidential Information and shall use it only in
# accordance with the terms of the license agreement you entered into
# with FLIR Integrated Imaging Solutions, Inc. (FLIR).
#
# FLIR MAKES NO REPRESENTATIONS OR WARRANTIES ABOUT THE SUITABILITY OF THE
# SOFTWARE, EITHER EXPRESSED OR IMPLIED, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
# PURPOSE, OR NON-INFRINGEMENT. FLIR SHALL NOT BE LIABLE FOR ANY DAMAGES
# SUFFERED BY LICENSEE AS A RESULT OF USING, MODIFYING OR DISTRIBUTING
# THIS SOFTWARE OR ITS DERIVATIVES.
# =============================================================================
#
# NodeMapInfo_QuickSpin.py shows how to interact with nodes
# using the QuickSpin API. QuickSpin is a subset of the Spinnaker library
# that allows for simpler node access and control.
#
# This example demonstrates the retrieval of information from both the
# transport layer and the camera. Because the focus of this example is node
# access, which is where QuickSpin and regular Spinnaker differ, this
# example differs from NodeMapInfo quite a bit.
#
# A much wider range of topics is covered in the full Spinnaker examples than
# in the QuickSpin ones. There are only enough QuickSpin examples to
# demonstrate node access and to get started with the API; please see full
# Spinnaker examples for further or specific knowledge on a topic.
#
# Please leave us feedback at: https://www.surveymonkey.com/r/TDYMVAPI
# More source code examples at: https://github.com/Teledyne-MV/Spinnaker-Examples
# Need help? Check out our forum at: https://teledynevisionsolutions.zendesk.com/hc/en-us/community/topics

import PySpin
import sys


def print_node_info(node):
    """
    Prints node information if applicable

    *** NOTES ***
    Notice that each node is checked for availablility and readability prior
    to value retrieval. Checking for availability and readability (or writability
    when applicable) whenever a node is accessed is important in terms of error
    handling. If a node retrieval error occurs but remains unhandled, an exception
    is thrown.

    :param node: Node to get information from.
    :type node: INode
    """
    if node is not None and PySpin.IsReadable(node):
        print(PySpin.CValuePtr(node).ToString())
    else:
        print('unavailable')


def print_transport_layer_device_info(cam):
    """
    Prints device information from the transport layer.

    *** NOTES ***
    In QuickSpin, accessing device information on the transport layer is
    accomplished via a camera's TLDevice property. The TLDevice property
    houses nodes related to general device information such as the three
    demonstrated below, device access status, XML and GUI paths and
    locations, and GEV information to name a few. The TLDevice property
    allows access to nodes that would generally be retrieved through the
    TL device nodemap in full Spinnaker.

    Notice that each node is checked for availability and readability
    prior to value retrieval. Checking for availability and readability
    (or writability when applicable) whenever a node is accessed is
    important in terms of error handling. If a node retrieval error
    occurs but remains unhandled, an exception is thrown.

    :param cam: Camera to get information from.
    :type cam: CameraPtr
    :return: True if successful, False otherwise.
    :rtype: bool
    """
    try:
        result = True

        # Print device serial number
        print('Device serial number: ', end='')
        print_node_info(cam.TLDevice.DeviceSerialNumber)

        # Print device vendor name
        #
        # *** NOTE ***
        # To check node readability/writability, you can either
        # compare its access mode with RO, RW, etc. or you can use
        # the IsReadable/IsWritable functions on the node.
        print('Device vendor name: ', end='')
        print_node_info(cam.TLDevice.DeviceVendorName)

        # Print device display name
        print('Device display name: ', end='')
        print_node_info(cam.TLDevice.DeviceDisplayName)

    except PySpin.SpinnakerException as ex:
        print('Error: %s' % ex)
        return False

    return result


def print_transport_layer_stream_info(cam):
    """
    Prints stream information from transport layer.

    *** NOTES ***
    In QuickSpin, accessing stream information on the transport layer is
    accomplished via a camera's TLStream property. The TLStream property
    houses nodes related to streaming such as the two demonstrated below,
    buffer information, and GEV packet information to name a few. The
    TLStream property allows access to nodes that would generally be
    retrieved through the TL stream nodemap in full Spinnaker.

    :param cam: Camera to get information from.
    :type cam: CameraPtr
    :return: True if successful, False otherwise.
    :rtype: bool
    """
    try:
        result = True

        # Print stream ID
        print('Stream ID: ', end='')
        print_node_info(cam.TLStream.StreamID)

        # Print stream type
        print('Stream type: ', end='')
        print_node_info(cam.TLStream.StreamType)

    except PySpin.SpinnakerException as ex:
        print('Error: %s' % ex)
        return False

    return result


def print_transport_layer_interface_info(interface):
    """
    Prints stream information from the transport layer.

    *** NOTES ***
    In QuickSpin, accessing interface information is accomplished via an
    interface's TLInterface property. The TLInterface property houses
    nodes that hold information about the interface such as the three
    demonstrated below, other general interface information, and
    GEV addressing information. The TLInterface property allows access to
    nodes that would generally be retrieved through the interface nodemap
    in full Spinnaker.

    Interface nodes should also always be checked for availability and
    readability (or writability when applicable). If a node retrieval
    error occurs but remains unhandled, an exception is thrown.

    :param interface: Interface to get information from.
    :type interface: InterfacePtr
    :return: True if successful, False otherwise.
    :rtype: bool
    """
    try:
        result = True

        # Print interface display name
        print('Interface display name: ', end='')
        print_node_info(interface.TLInterface.InterfaceDisplayName)

        # Print interface ID
        print('Interface ID: ', end='')
        print_node_info(interface.TLInterface.InterfaceID)

        # Print interface type
        print('Interface type: ', end='')
        print_node_info(interface.TLInterface.InterfaceType)

        """
        Print information specific to the interface's host adapter from 
        the transport layer
        
        *** NOTES ***
        This information can help in determining which interface to use
        for better performance as some host adapters may have more
        significant physical limitations.
        
        Interface nodes should also always be checked for availability
        readability (or writability when applicable). If a node retrieval
        error occurs but remains unhandled, an exception is thrown.
        """
        # Print host adapter name
        print('Host adapter name: ', end='')
        print_node_info(interface.TLInterface.HostAdapterName)

        # Print host adapter vendor name
        print('Host adapter vendor: ', end='')
        print_node_info(interface.TLInterface.HostAdapterVendor)

        # Print host adapter driver version
        print('Host adapter driver version: ', end='')
        print_node_info(interface.TLInterface.HostAdapterDriverVersion)

        print()
    except PySpin.SpinnakerException as ex:
        print('Error: %s' % ex)
        return False

    return result


def print_genicam_device_info(cam):
    """
    Prints device information from the camera.

    *** NOTES ***
    Most camera interaction happens through GenICam nodes. The
    advantages of these nodes is that there is a lot more of them, they
    allow for a much deeper level of interaction with a camera, and no
    intermediate property (i.e. TLDevice or TLStream) is required. The
    disadvantage is that they require initialization.

    :param cam: Camera to get information from.
    :type cam: CameraPtr
    :return: True if successful, False otherwise.
    :rtype: bool
    """
    try:
        result = True

        # Print exposure time
        print('Exposure time: ', end='')
        print_node_info(cam.ExposureTime)

        # Print black level
        print('Black level: ', end='')
        print_node_info(cam.BlackLevel)

        # Print height
        print('Height: ', end='')
        print_node_info(cam.Height)

    except PySpin.SpinnakerException as ex:
        print('Error: %s' % ex)
        return False

    return result


def main():
    """
    Example entry point; this function prints transport layer information from
    each interface and transport and GenICam information from each camera.

    :return: True if successful, False otherwise.
    :rtype: bool
    """
    result = True

    # Retrieve singleton reference to system object
    sys = PySpin.System.GetInstance()

    # Get current library version
    version = sys.GetLibraryVersion()
    print('Library version: %d.%d.%d.%d' % (version.major, version.minor, version.type, version.build))

    # Retrieve list of cameras from the system
    cam_list = sys.GetCameras()

    num_cams = cam_list.GetSize()

    print('Number of cameras detected: %i \n' % num_cams)

    # Finish if there are no cameras
    if num_cams == 0:
        # Clear camera list before releasing system
        cam_list.Clear()
        
        # Release system instance
        sys.ReleaseInstance()
        
        print('Not enough cameras!')
        input('Done! Press Enter to exit...')
        return False

    # Retrieve list of interfaces from the system 
    iface_list = sys.GetInterfaces()

    num_ifaces = iface_list.GetSize()

    print('Number of interfaces detected: %i \n' % num_ifaces)

    # Print information on each interface
    #
    # *** NOTES ***
    # All USB 3 Vision and GigE Vision interfaces should enumerate for
    # Spinnaker.
    print('\n*** PRINTING INTERFACE INFORMATION ***\n')

    for iface in iface_list:
        result &= print_transport_layer_interface_info(iface)

    # Release reference to interface
    # NOTE: Unlike the C++ examples, we cannot rely on pointer objects being automatically
    # cleaned up when going out of scope.
    # The usage of del is preferred to assigning the variable to None.
    del iface

    # Print general device information on each camera from transport layer
    #
    # *** NOTES ***
    # Transport layer nodes do not require initialization in order to interact
    # with them.
    print('\n*** PRINTING TRANSPORT LAYER DEVICE INFORMATION ***\n')

    for cam in cam_list:
        result &= print_transport_layer_device_info(cam)

    # Print streaming information on each camera from transport layer
    #
    # *** NOTES ***
    # Again, initialization is not required to print information from the
    # transport layer; this is equally true of streaming information.
    print('\n*** PRINTING TRANSPORT LAYER STREAMING INFORMATION ***\n')

    for cam in cam_list:
        result &= print_transport_layer_stream_info(cam)

    # Print device information on each camera from GenICam nodemap
    #
    # *** NOTES ***
    # GenICam nodes require initialization in order to interact with
    # them; as such, this loop initializes the camera, prints some information
    # from the GenICam nodemap, and then deinitializes it. If the camera were
    # not initialized, node availability would fail.
    print('\n*** PRINTING GENICAM INFORMATION ***\n')

    for cam in cam_list:
        # Initialize camera
        cam.Init()

        # Print info
        result &= print_genicam_device_info(cam)

        # Deinitialize camera
        cam.DeInit()

    # Release reference to camera
    # NOTE: Unlike the C++ examples, we cannot rely on pointer objects being automatically
    # cleaned up when going out of scope.
    # The usage of del is preferred to assigning the variable to None.
    del cam

    # Clear camera list before releasing system
    cam_list.Clear()

    # Clear interface list before releasing system
    iface_list.Clear()

    # Release system instance
    sys.ReleaseInstance()

    input('\nDone! Press Enter to exit...')
    return result

if __name__ == '__main__':
    if main():
        sys.exit(0)
    else:
        sys.exit(1)
