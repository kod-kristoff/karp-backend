import logging
import re
import json
import elasticsearch_dsl as es_dsl  # pyre-ignore

from karp.query_dsl import basic_ast as ast
from karp import query_dsl
from karp import search


logger = logging.getLogger('karp')


class EsQuery(search.Query):
    def __init__(self):
        super().__init__()
        self.query = None
        self.resource_str = None

    def parse_arguments(self, args, resource_str):
        super().parse_arguments(args, resource_str)
        self.resource_str = resource_str
        if not self.ast.is_empty():
            self.query = create_es_query(self.ast.root)

    def _self_name(self) -> str:
        return 'EsQuery query={} resource_str={}'.format(self.query,
                                                         self.resource_str)


def get_value(value_node):
    if isinstance(value_node, ast.StringNode):
        return value_node.value
    elif isinstance(value_node, ast.IntNode):
        return value_node.value
    elif isinstance(value_node, ast.FloatNode):
        return value_node.value
    else:
        raise NotImplementedError()


def create_es_query(node):
    if node is None:
        raise TypeError()

    q = None
    if isinstance(node, ast.UnaryOp):
        op = node.value
        values = []
        if node.child0.value in [query_dsl.Operators.AND, query_dsl.Operators.OR, query_dsl.Operators.NOT]:
            for child in node.child0.children():
                values.append(child.value)
            print('values = {}'.format(values))
        if op == query_dsl.Operators.NOT:
            q = ~create_es_query(node.child0)
        else:
            if op == query_dsl.Operators.FREETEXT:
                def freetext_query(node):
                    if isinstance(node, ast.StringNode):
                        return es_dsl.Q('multi_match', query=node.value, fuzziness=1)
                    else:
                        return es_dsl.Q('multi_match', query=node.value)
                if not values:
                    q = freetext_query(node.child0)
                else:
                    queries = [freetext_query(n) for n in node.child0.children()]
                    if node.child0.value == query_dsl.Operators.OR:
                        q = es_dsl.Q('bool', should=queries)
                    elif node.child0.value == query_dsl.Operators.AND:
                        q = es_dsl.Q('bool', must=queries)
                    else:
                        q = es_dsl.Q('bool', must_not=queries)
            elif op == query_dsl.Operators.FREERGXP:
                kwargs = {
                    'default_field': '*'
                }
                if not values:
                    kwargs['query'] = '/{}/'.format(node.child0.value)
                else:
                    if node.child0.value == query_dsl.Operators.OR:
                        operator = ' OR '
                    elif node.child0.value == query_dsl.Operators.AND:
                        operator = ' AND '
                    else:
                        raise RuntimeError('NOT is not supported for FREERGXP')
                    kwargs['query'] = operator.join('(/{}/)'.format(v) for v in values)
                print('kwargs = {}'.format(kwargs))
                q = es_dsl.Q('query_string', **kwargs)
            elif op == query_dsl.Operators.EXISTS:
                if not values:
                    q = es_dsl.Q('exists', field=node.child0.value)
                else:
                    queries = [es_dsl.Q('exists', field=value) for value in values]
                    if node.child0.value == query_dsl.Operators.OR:
                        q = es_dsl.Q('bool', should=queries)
                    elif node.child0.value == query_dsl.Operators.AND:
                        q = es_dsl.Q('bool', must=queries)
                    else:
                        q = es_dsl.Q('bool', must_not=queries)
            elif op == query_dsl.Operators.MISSING:
                if not values:
                    q = es_dsl.Q('bool', must_not=es_dsl.Q('exists', field=node.child0.value))
                else:
                    if node.child0.value == query_dsl.Operators.NOT:
                        q = es_dsl.Q('exists', field=values[0])
                    else:
                        queries = [es_dsl.Q('exists', field=value) for value in values]

                        if node.child0.value == query_dsl.Operators.AND:
                            q = es_dsl.Q('bool', must_not=queries)
                        else:
                            q = None
                            for query in queries:
                                q_tmp = es_dsl.Q('bool', must_not=query)
                                if not q:
                                    q = q_tmp
                                else:
                                    q = q | q_tmp
            else:
                raise RuntimeError('not implemented')
    elif isinstance(node, ast.BinaryOp):
        op = node.value
        arg1 = node.child0
        arg2 = node.child1

        # TODO this check breaks and and or since they always (?) have ast.ArgNode as parameters
        # if not isinstance(arg1, ast.ArgNode) or not isinstance(arg2, ast.ArgNode):
            # TODO these need to be moved outside of current query, for example:
            # "equals|name||or|Partille|Kumla" could be expressed in two ways
            # es_dsl.Q('terms', name=['Partille', 'Kumla'])
            # or
            # es_dsl.Q('bool', should=[es_dsl.Q('term', name='Partille'), es_dsl.Q('term', name='Kumla')])
            # but "regexp|name||or|Part*|Kum*"
            # can only be expressed as in the longer form above
            # raise RuntimeError()

        if op in [query_dsl.Operators.AND, query_dsl.Operators.OR]:
            # TODO check minimum should match rules in different contexts
            q1 = create_es_query(arg1)
            q2 = create_es_query(arg2)
            if op == query_dsl.Operators.AND:
                q = es_dsl.Q('bool', must=[q1, q2])
            else:
                q = es_dsl.Q('bool', should=[q1, q2])
        elif op == query_dsl.Operators.EQUALS:
            arg11 = get_value(arg1)
            arg22 = get_value(arg2)
            kwargs = {
                arg11: {
                    'query': arg22,
                    'operator': 'and'
                }
            }
            q = es_dsl.Q('match', **kwargs)
        elif op in [query_dsl.Operators.REGEXP,
                    query_dsl.Operators.CONTAINS,
                    query_dsl.Operators.STARTSWITH,
                    query_dsl.Operators.ENDSWITH]:
            def extract_field_plus_rawfield(field: str):
                if field.endswith('.raw'):
                    return [field]
                else:
                    return [field, field + '.raw']
            arg11 = extract_field_plus_rawfield(get_value(arg1))
            arg22 = get_value(arg2)

            if op == query_dsl.Operators.CONTAINS:
                arg22 = '.*' + re.escape(arg22) + '.*'
            elif op == query_dsl.Operators.STARTSWITH:
                arg22 = re.escape(arg22) + '.*'
            elif op == query_dsl.Operators.ENDSWITH:
                arg22 = '.*' + re.escape(arg22)
            # Construct query
            if len(arg11) == 1:
                q = es_dsl.Q('regexp', **{arg11[0]: arg22})
            else:
                q = es_dsl.Q('bool', should=[es_dsl.Q('regexp', **{field: arg22}) for field in arg11])
        elif op in [query_dsl.Operators.LT, query_dsl.Operators.LTE, query_dsl.Operators.GT, query_dsl.Operators.GTE]:
            range_args = {}
            arg11 = get_value(arg1)
            arg22 = get_value(arg2)
            if op == query_dsl.Operators.LT:
                range_args['lt'] = arg22
            elif op == query_dsl.Operators.LTE:
                range_args['lte'] = arg22
            elif op == query_dsl.Operators.GT:
                range_args['gt'] = arg22
            elif op == query_dsl.Operators.GTE:
                range_args['gte'] = arg22
            q = es_dsl.Q('range', **{arg11: range_args})
    elif isinstance(node, ast.TernaryOp):
        op = node.value
        arg1 = node.child0
        arg2 = node.child1
        arg3 = node.child2
        if op == query_dsl.Operators.RANGE:
            raise RuntimeError('don\'t now what to do yet')
        else:
            raise RuntimeError('what operators?')
    else:
        raise ValueError('Unknown query op %s' % node)

    return q


class EsSearch(search.SearchInterface):

    def __init__(self, es):
        self.es = es
        self.analyzed_fields = self._init_field_mapping()

    def _init_field_mapping(self):
        """
        Create a field mapping based on the mappings of elasticsearch
        currently the only information we need is if a field is analyzed (i.e. text)
        or not.
        """
        def parse_mapping(properties):
            analyzed_fields = []
            for prop_name, prop_values in properties.items():
                if 'properties' in prop_values:
                    res = parse_mapping(prop_values['properties'])
                    analyzed_fields.extend([prop_name + '.' + prop for prop in res])
                else:
                    if prop_values['type'] == 'text':
                        analyzed_fields.append(prop_name)
            return analyzed_fields

        field_mapping = {}

        # Doesn't work for tests, can't find resource_definition
        # for resource in resourcemgr.get_available_resources():
        #     mapping = self.es.indices.get_mapping(index=resource.resource_id)
        #     field_mapping[resource.resource_id] = parse_mapping(
        #         next(iter(mapping.values()))['mappings']['entry']['properties']
        #     )
        aliases = self._get_all_aliases()
        mapping = self.es.indices.get_mapping()
        for (alias, index) in aliases:
            if ('mappings' in mapping[index] and
                'entry' in mapping[index]['mappings'] and
                'properties' in mapping[index]['mappings']['entry']):
                field_mapping[alias] = parse_mapping(
                    mapping[index]['mappings']['entry']['properties']
                )
        return field_mapping

    def _get_all_aliases(self):
        """
        :return: a list of tuples (alias_name, index_name)
        """
        result = self.es.cat.aliases(h='alias,index')
        index_names = []
        for index_name in result.split('\n')[:-1]:
            if index_name[0] != '.':
                groups = re.search(r'([^ ]*) +(.*)', index_name).groups()
                alias = groups[0]
                index = groups[1]
                index_names.append((alias, index))
        return index_names

    def build_query(self, args, resource_str: str) -> EsQuery:
        query = EsQuery()
        query.parse_arguments(args, resource_str)
        return query

    def _format_result(self, resource_ids, response):

        def format_entry(entry):
            dict_entry = entry.to_dict()
            version = dict_entry.pop('_entry_version')
            return {
                'id': entry.meta.id,
                'version': version,
                'resource': next(resource for resource in resource_ids if entry.meta.index.startswith(resource)),
                'entry': dict_entry
            }

        result = {
            'total': response.hits.total,
            'hits': [format_entry(entry) for entry in response]
        }
        return result

    def search_with_query(self, query: EsQuery):
        logger.info('search_with_query called with query={}'.format(query))
        if query.split_results:
            ms = es_dsl.MultiSearch(using=self.es)

            for resource in query.resources:
                s = es_dsl.Search(index=resource)

                if query.query is not None:
                    s = s.query(query.query)
                s = s[query.from_:query.from_ + query.size]
                ms = ms.add(s)

            responses = ms.execute()
            result = {
                'total': 0
            }
            for i, response in enumerate(responses):
                result[query.resources[i]] = self._format_result(query.resources, response)
                result['total'] += response.hits.total
                if query.lexicon_stats:
                    if 'distribution' not in result:
                        result['distribution'] = {}
                    result['distribution'][query.resources[i]] = response.hits.total

            return result
        else:
            s = es_dsl.Search(using=self.es, index=query.resource_str)
            logger.debug('s = {}'.format(s))
            if query.query is not None:
                s = s.query(query.query)

            s = s[query.from_:query.from_ + query.size]

            if query.lexicon_stats:
                s.aggs.bucket('distribution', 'terms', field='_index', size=len(query.resources))

            response = s.execute()

            logger.debug('response = {}'.format(response.to_dict()))

            result = self._format_result(query.resources, response)
            if query.lexicon_stats:
                for bucket in response.aggregations.distribution.buckets:
                    key = bucket['key']
                    value = bucket['doc_count']
                    if 'distribution' not in result:
                        result['distribution'] = {}
                    result['distribution'][key.rsplit('_', 1)[0]] = value

            return result

    def search_ids(self, args, resource_id: str, entry_ids: str):
        logger.info('Called EsSearch.search_ids(self, args, resource_id, entry_ids) with:')
        logger.info('  resource_id = {}'.format(resource_id))
        logger.info('  entry_ids = {}'.format(entry_ids))
        entries = entry_ids.split(',')
        query = es_dsl.Q('terms', _id=entries)
        logger.debug('query = {}'.format(query))
        s = es_dsl.Search(using=self.es, index=resource_id).query(query)
        logger.debug('s = {}'.format(s.to_dict()))
        response = s.execute()

        return self._format_result([resource_id], response)

    def statistics(self, resource_id: str, field: str):
        s = es_dsl.Search(using=self.es, index=resource_id)
        s = s[0:0]

        if field in self.analyzed_fields[resource_id]:
            field = field + '.raw'

        logger.debug('Statistics: analyzed fields are:')
        logger.debug(json.dumps(self.analyzed_fields, indent=4))
        logger.debug('Doing aggregations on resource_id: {resource_id}, on field {field}'.format(
            resource_id=resource_id,
            field=field
        ))
        s.aggs.bucket('field_values', 'terms', field=field, size=2147483647)
        response = s.execute()
        result = []
        for bucket in response.aggregations.field_values.buckets:
            result.append({'value': bucket['key'], 'count': bucket['doc_count']})
        return result
