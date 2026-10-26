"""Bytecode instruction opcodes for the Lyslyn Virtual Machine."""
from enum import IntEnum


class OpCode(IntEnum):
    OP_CONSTANT = 0
    OP_NIL = 1
    OP_TRUE = 2
    OP_FALSE = 3

    OP_POP = 4
    OP_DUP = 5

    OP_DEF_GLOBAL = 10
    OP_GET_GLOBAL = 11
    OP_SET_GLOBAL = 12
    OP_GET_LOCAL = 13
    OP_SET_LOCAL = 14
    OP_GET_UPVALUE = 15
    OP_SET_UPVALUE = 16

    OP_ADD = 20
    OP_SUB = 21
    OP_MUL = 22
    OP_DIV = 23
    OP_MOD = 24
    OP_NEG = 25

    OP_EQUAL = 30
    OP_GREATER = 31
    OP_LESS = 32
    OP_NOT = 33

    OP_JUMP = 40
    OP_JUMP_IF_FALSE = 41
    OP_LOOP = 42

    OP_CALL = 50
    OP_CLOSURE = 51
    OP_RETURN = 52

    OP_BUILD_LIST = 60
    OP_BUILD_MAP = 61
    OP_INDEX_GET = 62
    OP_INDEX_SET = 63

    OP_PRINT = 70

    OP_HALT = 99
