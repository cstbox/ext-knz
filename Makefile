# CSTBox framework
#
# Makefile for building the Debian distribution package containing the
# Kipp and Zonen  Modbus products support.
#
# author = Eric PASCUAL - CSTB (eric.pascual@cstb.fr)

# name of the CSTBox module
MODULE_NAME=ext-knz

include $(CSTBOX_DEVEL_HOME)/lib/makefile-dist.mk

copy_files: \
	check_metadata_files \
	copy_python_files 

