#!/bin/bash
mkdir build
pushd build
cmake $@ ../src
make
popd
