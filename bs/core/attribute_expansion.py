import logging
import math


logger = logging.getLogger(__name__)

ATTRIBUTE_EXPANSION_TYPE_PREFIX = 'Attribute Expanded'
ATTRIBUTE_EXPANSION_ATTRIBLIST_SUFFIX = '_attriblist'


def is_expandable_type(attribute_type):

    atype_name = attribute_type.name
    return atype_name.startswith(ATTRIBUTE_EXPANSION_TYPE_PREFIX)


def get_attriblist_str(attribute_name, resources=[], allocations=[]):

    attriblist_name = "{aname}{suffix}".format(
        aname=attribute_name, suffix=ATTRIBUTE_EXPANSION_ATTRIBLIST_SUFFIX)
    attriblist = None

    for res in resources:
        alist_list = res.get_attribute_list(attriblist_name)
        for alist in alist_list:
            if attriblist:
                attriblist = attriblist + '\n' + alist
            else:
                attriblist = alist
    for alloc in allocations:
        alist_list = alloc.get_attribute_list(attriblist_name)
        for alist in alist_list:
            if attriblist:
                attriblist = attriblist + '\n' + alist
            else:
                attriblist = alist

    return attriblist


def get_attribute_parameter_value(
        argument, attribute_parameter_dict, error_text,
        resources=[], allocations=[]):
    value = None

    if argument.startswith("'"):
        tmpstr = argument[1:]
        tmp = tmpstr[-1:]
        if tmp == "'":
            tmpstr = tmpstr[:-1]
            return tmpstr
        else:
            logger.warn(" 处理时发现错误的字符串文本'{}' "
                        "{}; 缺少单引号".format(
                            argument, error_text))
            return None

    attrib_source = None
    attrib_sources = [':APDICT', 'RESOURCE:', 'ALLOCATION:', ':']
    for asrc in attrib_sources:
        if argument.startswith(asrc):
            attrib_source = asrc
            tmplen = len(asrc)
            argument = argument[tmplen:]
            break

    if (attribute_parameter_dict is not None and
            (attrib_source == ':' or attrib_source == 'APDICT:')):
        if argument in attribute_parameter_dict:
            return attribute_parameter_dict[argument]

    if attrib_source == ':' or attrib_source == 'ALLOCATION:':
        for alloc in allocations:
            tmp = alloc.get_attribute(argument)
            if tmp is not None:
                return tmp

    if attrib_source == ':' or attrib_source == 'RESOURCE:':
        for res in resources:
            tmp = res.get_attribute(argument)
            if tmp is not None:
                return tmp

    if attrib_source is not None:
        return None

    try:
        value = int(argument)
        return value
    except ValueError:
        try:
            value = float(argument)
            return value
        except ValueError:
            logger.warn("无法计算参数'{arg}' 当 "
                        "运行 {etxt}, 返回无".format(
                            arg=argument, etxt=error_text))
            return None

    return None


def process_attribute_parameter_operation(
        opcode, oldvalue, argument, error_text):
    if argument is None:
        logger.warn("{}没出现在 {}中, "
                    "无返回值".format(opcode, error_text))
        return None
    if oldvalue is None:
        if opcode != ':' and opcode != '|':
            logger.warn(" {}没出现在 {}中, "
                        "无返回值".format(opcode, error_text))
            return None

    try:
        if opcode == ':':
            return argument
        if opcode == '|':
            if oldvalue is None:
                return argument
            else:
                return oldvalue
        if opcode == '+':
            if isinstance(oldvalue, int) or isinstance(oldvalue, float):
                newval = oldvalue + argument
                return newval
            elif isinstance(oldvalue, str):
                newval = oldvalue + argument
                return newval
            else:
                logger.warn(' {} 作用于类型的参数 '
                            '{} 在 {}, 无返回值'.format(
                                opcode, type(oldvalue), error_text))
                return None
        if opcode == '-':
            newval = oldvalue - argument
            return newval
        if opcode == '*':
            newval = oldvalue * argument
            return newval
        if opcode == '/':
            newval = oldvalue / argument
            return newval
        if opcode == '(':
            if argument == 'floor':
                newval = math.floor(oldvalue)
            else:
                logger.error('无法识别的函数命名 {} 在 {} '
                             '{},无返回值'.format(
                                 argument, opcode, error_text))
                return None
        logger.error('无法识别的操作 {}在 {}, '
                     '无返回值'.format(opcode, error_text))
    except Exception as xcept:
        logger.warn("执行运算符时出错{op} 旧值='{old}' "
                    "{arg} 在 {errtext}".format(
                        op=opcode, old=oldvalue, arg=argument, errtext=error_text))
        return None


def process_attribute_parameter_string(
        parameter_string, attribute_name, attribute_parameter_dict={},
        resources=[], allocations=[]):
    parmstr = parameter_string.strip()
    if not parmstr:
        return attribute_parameter_dict
    if parmstr.startswith('#'):
        return attribute_parameter_dict

    tmp = parmstr.split('=', 1)
    if len(tmp) != 2:
        logger.error("参数字符串 '{pstr}', 没有 '=' "
                     "创建用于扩展的属性参数字典 "
                     "属性 {aname}".format(
                         aname=attribute_name, pstr=parameter_string))
        return attribute_parameter_dict
    pname = tmp[0]
    argument = tmp[1].strip()
    opcode = pname[-1:]
    pname = pname[:-1].strip()

    value = None
    if opcode == '(':
        value = argument
    else:
        error_text = 'attribute_parameter_string={pstr} ' \
            '用于扩展属性 {aname}'.format(
                pstr=parameter_string, aname=attribute_name)
        value = get_attribute_parameter_value(
            argument=argument,
            attribute_parameter_dict=attribute_parameter_dict,
            resources=resources,
            allocations=allocations,
            error_text=error_text)

    if pname in attribute_parameter_dict:
        oldval = attribute_parameter_dict[pname]
    else:
        oldval = None

    newval = process_attribute_parameter_operation(
        opcode=opcode, oldvalue=oldval, argument=value,
        error_text=error_text)
    attribute_parameter_dict[pname] = newval
    return attribute_parameter_dict


def make_attribute_parameter_dictionary(attribute_name,
                                        attribute_parameter_string, resources=[], allocations=[]):

    apdict = dict()

    attrib_parm_list = list(map(str.strip,
                                attribute_parameter_string.splitlines()))
    for parmstr in attrib_parm_list:
        apdict = process_attribute_parameter_string(
            parameter_string=parmstr,
            attribute_parameter_dict=apdict,
            attribute_name=attribute_name,
            resources=resources,
            allocations=allocations)
    return apdict


def expand_attribute(raw_value, attribute_name, attriblist_string,
                     resources=[], allocations=[]):
    try:
        apdict = make_attribute_parameter_dictionary(
            attribute_parameter_string=attriblist_string,
            attribute_name=attribute_name,
            resources=resources,
            allocations=allocations)

        expanded = raw_value.format(**apdict)
        return expanded
    except Exception as xcept:
        logger.error("展开时出错 {aname}: {error}".format(
            aname=attribute_name, error=xcept))
        return raw_value


def convert_type(value, type_name, error_text='unknown'):
    if type_name is None:
        logger.error('找不到属性类型 {}'.format(error_text))
        return value

    if type_name.endswith('Text'):
        try:
            newval = str(value)
            return newval
        except ValueError:
            logger.error('Error converting "{}" to {} in {}'.format(
                value, 'Text', error_text))
            return value

    if type_name.endswith('Int'):
        try:
            newval = int(value)
            return newval
        except ValueError:
            logger.error('Error converting "{}" to {} in {}'.format(
                value, 'Int', error_text))
            return value

    if type_name.endswith('Float'):
        try:
            newval = float(value)
            return newval
        except ValueError:
            logger.error('Error converting "{}" to {} in {}'.format(
                value, 'Float', error_text))
            return value

    return value
