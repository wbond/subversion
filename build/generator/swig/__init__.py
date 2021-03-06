#
#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#
#
#
# generator.swig: Base class for SWIG-related generators
#

import os
import re
import shutil
import generator.util.executable as _exec
from generator.gen_base import _collect_paths
try:
  # Python >=3.0
  import configparser
except ImportError:
  # Python <3.0
  import ConfigParser as configparser

class Generator:
  """Base class for SWIG-related generators"""
  langs = ["python", "perl", "ruby"]
  short = { "perl": "pl", "python": "py", "ruby": "rb" }

  def __init__(self, conf, swig_path):
    """Read build.conf"""

    # Now read and parse build.conf
    parser = configparser.ConfigParser()
    parser.read(conf)

    # Read configuration options
    self.proxy_dir = parser.get('options', 'swig-proxy-dir')
    self.includes = _collect_paths(parser.get('options', 'includes'))
    self.swig_checkout_files = \
      _collect_paths(parser.get('options', 'swig-checkout-files'))

    # Calculate build options
    self.opts = {}
    for lang in self.langs:
      self.opts[lang] = parser.get('options', 'swig-%s-opts' % lang)

    # Calculate SWIG paths
    self.swig_path = swig_path
    try:
      self.swig_libdir = _exec.output([self.swig_path, "-swiglib"], strip=1)
    except AssertionError:
      pass

  def version(self):
    """Get the version number of SWIG"""
    try:
      swig_version = _exec.output([self.swig_path, "-version"])
      m = re.search("Version (\d+).(\d+).(\d+)", swig_version)
      if m:
        return (m.group(1), m.group(2), m.group(3))
    except AssertionError:
      pass
    return (0, 0, 0)

