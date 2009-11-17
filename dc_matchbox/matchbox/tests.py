

from datetime import datetime
from uuid import uuid4
import unittest

from dcdata.contribution.models import Contribution, sql_names
from dcdata.models import Import
from models import Entity, EntityAlias, EntityAttribute, Normalization
from matchbox_scripts.support.build_entities import populate_entities
from matchbox_scripts.support.normalize_database import normalize
from strings.normalizer import basic_normalizer
from matchbox.queries import search_entities_by_name, merge_entities, _prepend_pluses



class TestQueries(unittest.TestCase):

    def save_contribution(self, org_name, org_entity):
        c = Contribution(organization_name=org_name, 
                     organization_urn='urn:unittest:organization:' + org_name,
                     organization_entity=org_entity,
                     datestamp=datetime.now(),
                     cycle='09', 
                     transaction_namespace='urn:unittest:transaction',
                     import_reference=self.import_)
        c.save()
        

    def setUp(self):
        """ 
        to do: set up some basic transactions, the run the build_entities and normalize scripts.
        
        Also add an entity with no corresponding transactions.
        """
        
        print("Setting up database...")
        Import.objects.all().delete()
        Contribution.objects.all().delete()
        Entity.objects.all().delete()
        EntityAlias.objects.all().delete()
        EntityAttribute.objects.all().delete()
        Normalization.objects.all().delete()
        
        self.import_ = Import()
        self.import_.save()
        
        self.apple_id = uuid4().hex
        self.apricot_id = uuid4().hex
        
        for (org_name, org_entity) in [('Apple', self.apple_id), ('Apple Juice', self.apple_id), ('Apricot', self.apricot_id)]:
            self.save_contribution(org_name, org_entity)

        populate_entities(sql_names['contribution'], 
                          sql_names['contribution_organization_name'], 
                          sql_names['contribution_organization_entity'], 
                          [sql_names['contribution_organization_name']],
                          [sql_names['contribution_organization_urn']])
        
        orphan = Entity(name=u'Avacado')
        orphan.save()
        orphan.aliases.create(alias=u'Avacado')
        
        normalize([('entityalias', ['entityalias_alias'])], basic_normalizer)
        
        
    def test_populate_entities(self):
        self.assertEqual(3, Entity.objects.count())
        
        apple = Entity.objects.get(name="Apple")
        self.assertEqual(2, Contribution.objects.with_entity(apple, ['organization_entity']).count())
        
        apple_alias = EntityAlias.objects.get(alias="Apple")
        self.assertEqual(apple.id, apple_alias.entity.id)
        
        self.assertEqual(3, apple.attributes.count())
        self.assertEqual(1, apple.attributes.filter(namespace='urn:unittest:organization', value='Apple').count())
        self.assertEqual(1, apple.attributes.filter(namespace='urn:unittest:organization', value='Apple Juice').count())
        self.assertEqual(1, apple.attributes.filter(namespace=EntityAttribute.ENTITY_ID_NAMESPACE, value=apple.id).count())


        apricot = Entity.objects.get(name="apricot")
        self.assertEqual(1, Contribution.objects.with_entity(apricot, ['organization_entity']).count())
        
        apricot_alias = EntityAlias.objects.get(alias="apricot")
        self.assertEqual(apricot.id, apricot_alias.entity.id)
        
        self.assertEqual(2, apricot.attributes.count())
        self.assertEqual(1, apricot.attributes.filter(namespace='urn:unittest:organization', value='Apricot').count())
        self.assertEqual(1, apricot.attributes.filter(namespace=EntityAttribute.ENTITY_ID_NAMESPACE, value=apricot.id).count())

        
        avacado = Entity.objects.get(name='avacado')
        self.assertEqual(0, Contribution.objects.with_entity(avacado, ['organization_entity']).count())
        

    def test_search_entities_by_name(self):
        result = search_entities_by_name(u'a')
        
        expected = [['Apple', 2], ['Apricot', 1], ['Avacado', 0]]
        
        for ((expected_name, expected_count), (id, name, count)) in zip(expected, result):
            self.assertEqual(expected_name, name)
            self.assertEqual(expected_count, count)
    
    def test_search_entities_by_name_multiple_aliases(self):
        apple = Entity.objects.get(name="Apple")
        apple.aliases.create(alias="Appetite")
        Normalization.objects.create(original="Appetite", normalized="appetite")
        
        result = search_entities_by_name(u'app')
        expected = [['Apple', 2]]

        for ((expected_name, expected_count), (id, name, count)) in zip(expected, result):
            self.assertEqual(expected_name, name)
            self.assertEqual(expected_count, count)
            
    def test_merge_entities(self):
        new_id = merge_entities((Entity.objects.get(name="Apple").id, Entity.objects.get(name="Apricot").id), Entity(name=u"Applicot"))
        
        self.assertEqual(2, Entity.objects.count())
        applicot = Entity.objects.get(name="Applicot")
        self.assertEqual(new_id, applicot.id)
        
        self.assertEqual(u'applicot', Normalization.objects.get(original="Applicot").normalized)
        
        self.assertEqual(3, Contribution.objects.with_entity(applicot, ['organization_entity']).count())
        
        self.assertEqual(4, applicot.aliases.count())
        self.assertEqual(1, applicot.aliases.filter(alias='Apple').count())
        self.assertEqual(1, applicot.aliases.filter(alias='Apple Juice').count())
        self.assertEqual(1, applicot.aliases.filter(alias='Apricot').count())
        self.assertEqual(1, applicot.aliases.filter(alias='Applicot').count())
        
    def test_merge_entities_alias_duplication(self):
        apple = Entity.objects.get(id=self.apple_id)
        apple.aliases.create(alias="Delicious")
        
        apricot = Entity.objects.get(id=self.apricot_id)
        apricot.aliases.create(alias="Delicious")
        
        merge_entities((apple.id, apricot.id), Entity(name=u'Applicot'))
        
        applicot = Entity.objects.get(name="Applicot")

        self.assertEqual(5, applicot.aliases.count())
        self.assertEqual(1, applicot.aliases.filter(alias='Apple').count())
        self.assertEqual(1, applicot.aliases.filter(alias='Apple Juice').count())
        self.assertEqual(1, applicot.aliases.filter(alias='Apricot').count())
        self.assertEqual(1, applicot.aliases.filter(alias='Applicot').count())
        self.assertEqual(1, applicot.aliases.filter(alias='Delicious').count())
        
    def test_merge_entities_attribute_duplication(self):
        apple = Entity.objects.get(id=self.apple_id)
        apple.attributes.all().delete()
        apple.attributes.create(namespace='color', value='red')
        apple.attributes.create(namespace='color', value='yellow')
        apple.attributes.create(namespace='texture', value='crisp')
        
        apricot = Entity.objects.get(id=self.apricot_id)
        apricot.attributes.all().delete()
        apricot.attributes.create(namespace='color', value='yellow')
        apricot.attributes.create(namespace='texture', value='soft')
        
        merge_entities((apple.id, apricot.id), Entity(name=u'Applicot'))
        
        applicot = Entity.objects.get(name="Applicot")
        
        self.assertEqual(5, applicot.attributes.count())
        self.assertEqual(1, applicot.attributes.filter(namespace='color', value='red').count())
        self.assertEqual(1, applicot.attributes.filter(namespace='color', value='yellow').count())
        self.assertEqual(1, applicot.attributes.filter(namespace='texture', value='crisp').count())
        self.assertEqual(1, applicot.attributes.filter(namespace='texture', value='soft').count())
        
    def test_merge_entities_previous_ids(self):
        merge_entities((self.apple_id, self.apricot_id), Entity(name=u'Applicot'))
        applicot = Entity.objects.get(name="Applicot")

        self.assertEqual(6, applicot.attributes.count())
        self.assertEqual(1, applicot.attributes.filter(namespace=EntityAttribute.ENTITY_ID_NAMESPACE, value=self.apple_id).count())
        self.assertEqual(1, applicot.attributes.filter(namespace=EntityAttribute.ENTITY_ID_NAMESPACE, value=self.apricot_id).count())
        self.assertEqual(1, applicot.attributes.filter(namespace=EntityAttribute.ENTITY_ID_NAMESPACE, value=applicot.id).count())
        self.assertEqual(1, applicot.attributes.filter(namespace='urn:unittest:organization', value='Apricot').count())
        self.assertEqual(1, applicot.attributes.filter(namespace='urn:unittest:organization', value='Apple Juice').count())
        self.assertEqual(1, applicot.attributes.filter(namespace='urn:unittest:organization', value='Apple').count())


    
class TestUtils(unittest.TestCase):
    def test_prepend_pluses(self):
        self.assertEqual("", _prepend_pluses(""))
        self.assertEqual("", _prepend_pluses("   "))
        
        self.assertEqual("+a", _prepend_pluses("a"))
        self.assertEqual("+apple +computer", _prepend_pluses("apple computer"))
        self.assertEqual("+apple +computer, +inc.", _prepend_pluses("apple computer, inc."))
        self.assertEqual("+Procter +& +Gamble", _prepend_pluses("Procter & Gamble"))
        self.assertEqual("+Emily's +List", _prepend_pluses("Emily's List"))
        