# -*- encoding: utf-8 -*-

from pyparsing import *

caps       = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
lowers     = caps.lower()
digits     = "0123456789"

_select = CaselessKeyword("select")
_update = CaselessKeyword("update")
_set = CaselessKeyword("set")
_from   = CaselessKeyword("from")
_where  = CaselessKeyword("where")
_on = CaselessKeyword("on")
_and  = CaselessKeyword("and")
_or = CaselessKeyword("or")
_left_join = CaselessKeyword("left join")
_right_join = Or([CaselessKeyword("right join"), CaselessKeyword(",")]).suppress()

number = Word( digits )
double_quoted_string = QuotedString("\"", "\\", "\"\"", unquoteResults=False)
single_quoted_string = QuotedString("'", "\\", "\'\'", unquoteResults=False)
back_quoted_string = QuotedString("`", "\\", unquoteResults=False)

open_paren = Literal("(")
close_paren = Literal(")")

select_statement = Forward()
field = Forward()
field_list = Forward()
where_clause = Forward()

field << Or([
	# subselects
	Group(Empty().setParseAction(replaceWith("::subselect")) +
		  open_paren +
		  select_statement +
		  close_paren), 
	# function call
	Group(Empty().setParseAction(replaceWith("::function")) +
		  Word( alphas+"_", alphas + digits + "_" ) + # function name
		  open_paren +
		  Optional(field_list) + # function arguments
		  close_paren), 
	Word( alphas+"_", alphas + digits + "_" ), # fieldname
	number, # number literal
	double_quoted_string, # quoted string literal
	single_quoted_string, # quoted string literal
	back_quoted_string,	# quoted fieldname
	Literal("*") # asterisk
	])
#field_list = Group(delimitedList( field ))
field_list << field + Optional("," + field_list)
select_field_list = Group(
	Empty().setParseAction(replaceWith("::field_list")) +
	field_list)

table = field
tables = Forward()
tables << Or([
	table + Optional(_right_join + tables),
	table + Optional(_left_join + tables + _on + where_clause),
	Group(open_paren.suppress()  +
		  table +
		  Optional(Or([_left_join, _right_join]) + tables) +
		  close_paren.suppress()) +
	Optional( Or([_left_join, _right_join]) + tables)
	])
tables = Group(
	Empty().setParseAction(replaceWith("::tables")) +
	tables)

compare_operator = Or([Literal("="), Literal(">"), Literal("<")])
artih_operator = Or([Literal("-"), Literal("+"), Literal("/"), Literal("*")])

expression = Group(
	Empty().setParseAction(replaceWith("::expression")) +
	Or([field + compare_operator + field, field]))

and_expression = Forward()
or_expression = Forward()

and_expression = Or([
	Group(and_expression + _and + and_expression),
	Group(open_paren + and_expression + _or + and_expression + close_paren),
	expression])

or_expression = Or([
	and_expression + _or + and_expression,
	and_expression])

where_clause << Group(
	Empty().setParseAction(replaceWith("::where_clause")) +
	or_expression)

select_statement << Group(
	Empty().setParseAction(replaceWith("::select")) +
	_select +
	select_field_list +
	Optional(
		_from +
		tables +
		Optional(_where + where_clause)))

expression_list = Forward()
expression_list << Group(
	expression + Optional("," + expression_list))

update_statement = _update + table + _set + expression_list + _where + where_clause
grammer = select_statement ^ update_statement
