# Copyright (c) 2017 Sony Corporation. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import io
import os
import sys
from os.path import abspath, dirname, join, exists

here = abspath(dirname(abspath(__file__)))
base = abspath(join(here, '../..'))

import code_generator_utils as utils
import yaml

def type_to_pack_format(typestring):
    fmt = None
    if typestring == 'bool':
        fmt = 'B'
    elif typestring == 'double' or typestring == 'float':
        fmt = 'f'
    elif typestring == 'int64':
        fmt = 'i'
    elif typestring == 'repeated int64' or typestring == 'Shape':
        fmt = 'iI'
    elif typestring == 'string':
        fmt = 'i'
    return fmt

def generate_cpp_utils(function_info):
    function_list = utils.info_to_list(function_info)
    utils.generate_from_template(
        join(base, 'src/nbla_utils/nnp_impl_create_function.cpp.tmpl'), function_info=function_info, function_list=function_list)


def generate_proto(function_info, solver_info):
    utils.generate_from_template(
        join(base, 'src/nbla/proto/nnabla.proto.tmpl'), function_info=function_info, solver_info=solver_info)


def generate_python_utils(function_info):
    utils.generate_from_template(
        join(base, 'python/src/nnabla/utils/load_function.py.tmpl'), function_info=function_info)
    utils.generate_from_template(
        join(base, 'python/src/nnabla/utils/save_function.py.tmpl'), function_info=function_info)


def generate_function_python_interface(function_info):
    utils.generate_from_template(
        join(base, 'python/src/nnabla/function.pyx.tmpl'), function_info=function_info)
    utils.generate_from_template(
        join(base, 'python/src/nnabla/function.pxd.tmpl'), function_info=function_info)
    utils.generate_from_template(
        join(base, 'python/src/nnabla/function_bases.py.tmpl'), function_info=function_info)


def generate_solver_python_interface(solver_info):
    utils.generate_from_template(
        join(base, 'python/src/nnabla/solver.pyx.tmpl'), solver_info=solver_info)
    utils.generate_from_template(
        join(base, 'python/src/nnabla/solver.pxd.tmpl'), solver_info=solver_info)

def generate_function_order(function_info):
    with open(join(base, 'python/src/nnabla/utils/converter/utils.py')) as f:
        exec(f.read())
    order_yaml = join(base, 'python/src/nnabla/utils/converter/function_order.yaml')
    order_info= None
    if exists(order_yaml):
        with open(order_yaml, 'r') as f:
            order_info = utils.load_yaml_ordered(f)

    if order_info is None:
        order_info= OrderedDict()    

    func_id = 0
    for func, func_info in function_info.items():
        fmt = ''
        if 'arguments' in func_info:
            fmt = '_'
            for arg, arg_info in func_info['arguments'].items():
                fmt += type_to_pack_format(arg_info['type'])

        name = func+fmt
        if name not in order_info:
            while func_id in order_info.values():
                func_id += 1
            order_info[name] = func_id
        
        func_id += 1

    ############### Check duplicated function ID.
    orders = {}
    result = True
    for func, func_id in order_info.items():
        if func_id not in orders:
            orders[func_id] = []
        else:
            result = False
        orders[func_id].append(func)
    if not result:
        print('')
        print('############################################## Errors in function_order.yaml(START)')
    for func_id, functions in orders.items():
        if len(functions) > 1:
            print('ID {} duplicated between [{}].'.format(func_id, functions))
    if not result:
        print('Correct ID in "python/src/nnabla/utils/converter/function_order.yaml" manually.')
        print('############################################## Errors in function_order.yaml(END)')
        print('')
        import sys
        sys.exit(-1)

    with open(order_yaml, 'w') as f:
        f.write('# Copyright (c) 2017 Sony Corporation. All Rights Reserved.\n')
        f.write('#\n')
        f.write('# Licensed under the Apache License, Version 2.0 (the "License");\n')
        f.write('# you may not use this file except in compliance with the License.\n')
        f.write('# You may obtain a copy of the License at\n')
        f.write('#\n')
        f.write('#     http://www.apache.org/licenses/LICENSE-2.0\n')
        f.write('#\n')
        f.write('# Unless required by applicable law or agreed to in writing, software\n')
        f.write('# distributed under the License is distributed on an "AS IS" BASIS,\n')
        f.write('# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.\n')
        f.write('# See the License for the specific language governing permissions and\n')
        f.write('# limitations under the License.\n')
        f.write('#\n')
        f.write('# DO NOT EDIT THIS FILE!\n')
        f.write('# THIS FILE IS GENERATED BY CODE GENERATOR BUT ITS COMMITTED INTO\n')
        f.write('# SOURCE TREE TO MAKE FUNCTION ID PERSIST.\n')
        f.write('\n')
        for func_id in sorted(orders.keys()):
            f.write('{}: {}\n'.format(orders[func_id][0], func_id))

def generate():
    version = sys.argv[1]
    
    function_info = utils.load_function_info(flatten=True)
    solver_info = utils.load_solver_info()
    function_types = utils.load_yaml_ordered(open(
        join(here, 'function_types.yaml'), 'r'))
    solver_types = utils.load_yaml_ordered(open(
        join(here, 'solver_types.yaml'), 'r'))
    utils.generate_init(function_info, function_types,
                        solver_info, solver_types)
    utils.generate_function_types(function_info, function_types)
    utils.generate_solver_types(solver_info, solver_types)
    utils.generate_version(join(base, 'python/src/nnabla/_version.py.tmpl'), base, version=version)
    utils.generate_version(join(base, 'src/nbla/version.cpp.tmpl'), base, version=version)
    utils.generate_version(join(base, 'doc/requirements.txt.tmpl'), base, version=version)
    generate_solver_python_interface(solver_info)
    generate_function_python_interface(function_info)
    generate_python_utils(function_info)
    generate_proto(function_info, solver_info)
    generate_cpp_utils(function_info)
    generate_function_order(function_info)

    # Generate function skeletons if new ones are added to functions.yaml and function_types.yaml.
    utils.generate_skeleton_function_impl(
        function_info, function_types)
    func_header_template = join(
        base,
        'include/nbla/function/function_impl.hpp.tmpl')
    utils.generate_skeleton_function_impl(
        function_info, function_types,
        template=func_header_template, output_format='%s.hpp')

    # TODO: solver skeleton generation


if __name__ == '__main__':
    generate()
