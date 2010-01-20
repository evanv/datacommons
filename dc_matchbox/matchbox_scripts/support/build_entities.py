

import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

import time
import logging
import csv
from datetime import datetime
from matchbox.models import EntityAttribute, sql_names
from matchbox_scripts.build_matchbox import log
from scripts.crp.denormalize import contributor_urn



def quote(value):
    return value.replace("\\","\\\\").replace("'","\\'")


from matchbox.models import Entity
from dcdata.contribution.models import Contribution


def build_entity(name, type, criteria):
    e = Entity.objects.create(name=name, type=type)
    
    for (match_column, match_value, entity_column) in criteria:
        Contribution.objects.filter(**dict([(match_column, match_value)])).update(**dict([(entity_column, e.id)]))
        


def big_hitters_to_whitelist(filename):
    def parse(crp_id, nimsp_id, name):
        crp_urn = contributor_urn(crp_id)
        nimsp_urn = 'urn:nimsp:contributor:' + nimsp_id
        return (name, 'organization', [('contributor_name', name, 'contributor_entity'),
                                       ('organization_name', name, 'organization_entity'),
                                       ('parent_organization_name', name, 'parent_organization_entity'),
                                       ('contributor_urn', nimsp_urn, 'contributor_entity'),
                                       ('organization_urn', nimsp_urn, 'organization_urn'),
                                       ('parent_organization_urn', nimsp_urn, 'parent_organization_entity'),
                                       ('contributor_urn', crp_urn, 'contributor_entity')])
    
    return [parse(*row) for row in csv.reader(open(filename))]
        


# this is the old implementaiton that I'll be replacing
def populate_entities(transaction_table, entity_id_column, name_columns, attribute_column,
                      type_determiner, type_column=None, reviewer=__name__, timestamp = datetime.now()):
    """
    Create the entities table based on transactional records.
    
    Uses the normalization table to find all unique names,
    then creates an entity for every unique name and links
    each matching transactional record to the entity.
    
    """
    
    from django.db import connection, transaction
    cursor = connection.cursor()
    
    def query_entity_data():
        loop_cursor = connection.cursor()
        
        names_clause = ", ".join(name_columns)
        type_clause = ', ' + type_column if type_column else ''
        
        columns = "%s, %s, %s %s" % (entity_id_column, attribute_column, names_clause, type_clause)
        
        stmt = """select %s 
                from %s 
                where %s is not null 
                group by %s""" \
                % (columns, transaction_table, entity_id_column, columns)
        loop_cursor.execute(stmt)
        return loop_cursor
    
    def attribute_name_value_pair(attribute):
        attribute = attribute.strip()
        last_colon = attribute.rfind(":")
        if (last_colon >= 0):
            return (attribute[0:last_colon], attribute[last_colon + 1:])
        else:
            return None

    def create_entity(id, aliases, attributes, types):
        if not id:
            return

        stmt = 'select 1 from %s where %s = %%s' % (sql_names['entity'], sql_names['entity_id'])
        cursor.execute(stmt, [id])
        if cursor.rowcount:
            # don't re-add existing aliases and attributes
            stmt = 'select %s from %s where %s = %%s' % (sql_names['entityalias_alias'], sql_names['entityalias'], sql_names['entityalias_entity'])
            cursor.execute(stmt, [id])
            aliases -= set([alias for (alias,) in cursor])

            stmt = 'select %s, %s from %s where %s = %%s' % \
                (sql_names['entityattribute_namespace'], sql_names['entityattribute_value'], sql_names['entityattribute'], sql_names['entityattribute_entity'])
            cursor.execute(stmt, [id])
            attributes -= set([(namespace, value) for (namespace, value) in cursor])

        else:
            attributes.add((EntityAttribute.ENTITY_ID_NAMESPACE, id))
            
            name = aliases.__iter__().next() if len(aliases) > 0 else 'Unknown'
            if callable(type_determiner):
                type_val = type_determiner(types)
            else:
                type_val = type_determiner
            
            stmt = 'insert into %s (%s, %s, %s, %s, %s) values (%%s, %%s, %%s, %%s, %%s)' % \
                (sql_names['entity'], sql_names['entity_id'], sql_names['entity_name'], sql_names['entity_type'], sql_names['entity_reviewer'], sql_names['entity_timestamp'])
            
            cursor.execute(stmt, [id, name, type_val, reviewer, timestamp])
            
        for alias in aliases:
            stmt = 'insert into %s (%s, %s) values (%%s, %%s)' % (sql_names['entityalias'], sql_names['entityalias_entity'], sql_names['entityalias_alias'])
            cursor.execute(stmt, [id, alias])
            
        for (namespace, value) in attributes:
            stmt = 'insert into %s (%s, %s, %s) values (%%s, %%s, %%s)' % \
                (sql_names['entityattribute'], sql_names['entityattribute_entity'], sql_names['entityattribute_namespace'], sql_names['entityattribute_value'])
            cursor.execute(stmt, [id, namespace, value])


    i = 0
    prev_id = None
    names = set()
    attributes = set()
    types = set()
    
    last_time = time.time()

    for row_tuple in query_entity_data():
        row = list(row_tuple)        
        row_id = row.pop(0)
        row_attribute = row.pop(0)
        row_names = row[:len(name_columns)]
        row_type = row.pop(len(name_columns)) if type_column else None    
            
        if prev_id != row_id:
            create_entity(prev_id, names, attributes, types)
            
            i += 1
            if i % 1000 == 0:
                transaction.commit()
                logging.debug("processed %d entities..." % i)
                
            if i % 1000000 == 0:
                new_time = time.time()
                logging.info("processing last million of %d million entities took %f seconds." % (i / 1000000, new_time - last_time))
                last_time = new_time
                
            prev_id = row_id
            names.clear()
            attributes.clear()
            types.clear()

        for name in row_names:
            if name:
                names.add(name)
        if row_attribute:
            (namespace, value) = attribute_name_value_pair(row_attribute) or ('', '')
            if namespace and value:
                attributes.add((namespace, value))
        if row_type:
            types.add(row_type)

    create_entity(prev_id, names, attributes, types)
    
    transaction.commit()


    