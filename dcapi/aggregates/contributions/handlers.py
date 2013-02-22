
from dcapi.aggregates.handlers import EntityTopListHandler, EntitySingletonHandler, TopListHandler, PieHandler, ALL_CYCLES, execute_one, execute_top, check_empty
from django.core.cache import cache
from piston.handler import BaseHandler


class OrgPartyBreakdownHandler(PieHandler):

    category_map = {'R': 'Republicans', 'D': 'Democrats'}
    default_key = 'Other'

    stmt = """
        select recipient_party, count, amount
        from agg_party_from_org
        where
            organization_entity = %s
            and cycle = %s
    """

class OrgLevelBreakdownHandler(PieHandler):

    category_map = {'urn:fec:transaction': 'Federal', 'urn:nimsp:transaction': 'State'}

    stmt = """
        select transaction_namespace, count, amount
        from agg_namespace_from_org
        where
            organization_entity = %s
            and cycle = %s
    """

class PolLocalBreakdownHandler(PieHandler):

    category_map = {'out-of-state': 'Out-of-State', 'in-state': 'In-State'}
    default_key = 'Unknown'

    stmt = """
        select local, count, amount
        from agg_local_to_politician
        where
            recipient_entity = %s
            and cycle = %s
    """

class PolContributorTypeBreakdownHandler(PieHandler):

    category_map = {'I': 'Individuals', 'C': 'PACs'}
    default_key = 'Unknown'

    stmt = """
        select contributor_type, count, amount
        from agg_contributor_type_to_politician
        where
            recipient_entity = %s
            and cycle = %s
    """

class IndivPartyBreakdownHandler(PieHandler):

    category_map = {'R': 'Republicans', 'D': 'Democrats'}
    default_key = 'Other'

    stmt = """
        select recipient_party, count, amount
        from agg_party_from_indiv
        where
            contributor_entity = %s
            and cycle = %s
    """


class PolContributorsHandler(EntityTopListHandler):
    fields = ['name', 'id', 'total_count', 'direct_count', 'employee_count', 'total_amount', 'direct_amount', 'employee_amount']

    stmt = """
        select organization_name, organization_entity, total_count, pacs_count, indivs_count, total_amount, pacs_amount, indivs_amount
        from agg_orgs_to_cand
        where
            recipient_entity = %s
            and cycle = %s
        order by total_amount desc
        limit %s
    """


class IndivOrgRecipientsHandler(EntityTopListHandler):

    fields = ['recipient_name', 'recipient_entity', 'count', 'amount']

    stmt = """
        select recipient_name, recipient_entity, count, amount
        from agg_orgs_from_indiv
        where
            contributor_entity = %s
            and cycle = %s
        order by amount desc
        limit %s
    """


class IndivPolRecipientsHandler(EntityTopListHandler):

    fields = ['recipient_name', 'recipient_entity', 'party', 'state', 'count', 'amount']

    stmt = """
        select recipient_name, recipient_entity, party, state, count, amount
        from agg_cands_from_indiv aci
            left join politician_metadata_latest_cycle_view on recipient_entity = entity_id
        where
            contributor_entity = %s
            and aci.cycle = %s
        order by amount desc
        limit %s
    """


class OrgRecipientsHandler(EntityTopListHandler):

    fields = ['name', 'id', 'party', 'state', 'total_count', 'direct_count', 'employee_count', 'total_amount', 'direct_amount', 'employee_amount']

    stmt = """
        select recipient_name, recipient_entity, party, state, total_count, pacs_count, indivs_count, total_amount, pacs_amount, indivs_amount
        from agg_cands_from_org aco
            left join politician_metadata_latest_cycle_view on recipient_entity = entity_id
        where
            organization_entity = %s
            and aco.cycle = %s
        order by total_amount desc
        limit %s
    """

class OrgPACRecipientsHandler(EntityTopListHandler):

    fields = ['name', 'id', 'total_count', 'direct_count', 'employee_count', 'total_amount', 'direct_amount', 'employee_amount']

    stmt = """
        select recipient_name, recipient_entity, total_count, pacs_count, indivs_count, total_amount, pacs_amount, indivs_amount
        from
            agg_pacs_from_org
        where
            organization_entity = %s
            and cycle = %s
        order by total_amount desc
        limit %s
    """

class OrgRecipientsLifetimeHandler(EntityTopListHandler):
    args = ['entity_id', 'cycle']

    fields = 'name id total_amount cycle committee is_chair is_ranking'.split()

    stmt = """
        with tmp_agg_cands_from_org_with_meta as (
            select
                recipient_name,
                recipient_entity,
                max(total_amount) as total_amount,
                aco.cycle,
                array_agg(name) as committee_names,
                bool_or(is_chair) as is_chair,
                bool_or(is_ranking) as is_ranking
            from
                agg_cands_from_org aco
                left join politician_metadata_latest_cycle_view on recipient_entity = entity_id
                left join politician_committee pc on aco.recipient_entity = pc.entity_id and aco.cycle = pc.cycle
            where
                organization_entity = %s
                and aco.cycle >= %s
                and ((pc.is_chair is null or pc.is_chair) or (pc.is_ranking is null or pc.is_ranking))
                --and seat not in ('federal:president', 'state:governor')
            group by recipient_name, recipient_entity, aco.cycle
        )
        select
            recipient_name,
            recipient_entity,
            coalesce(total_amount, 0) as total_amount,
            cycle,
            committee_names,
            is_chair,
            is_ranking
        from
            (
                select distinct recipient_entity, recipient_name, cycle
                from (select distinct cycle from tmp_agg_cands_from_org_with_meta) all_cycles
                cross join (select distinct recipient_entity, recipient_name from tmp_agg_cands_from_org_with_meta) all_recipients
            ) all_recipients_all_cycles
            left join tmp_agg_cands_from_org_with_meta aco using (recipient_entity, recipient_name, cycle)
        where (total_amount is null or total_amount >= 0)
        order by cycle, recipient_name, total_amount desc
    """


class IndustriesHandler(EntityTopListHandler):

    fields = ['name', 'id', 'count', 'amount', 'should_show_entity']

    stmt = """
        select industry as name, industry_entity as id, count, amount, coalesce(should_show_entity, 't') as should_show_entity
        from agg_industries_to_cand
        left join matchbox_industrymetadata on industry_entity = entity_id
        where
            recipient_entity = %s
            and cycle = %s
        order by amount desc
        limit %s
    """

class UnknownIndustriesHandler(EntitySingletonHandler):

    fields = 'count amount'.split()

    stmt = """
        select count, amount
        from agg_unknown_industries_to_cand
        where
            recipient_entity = %s
            and cycle = %s
    """


class SectorsHandler(EntityTopListHandler):

    fields = ['sector', 'count', 'amount']

    stmt = """
        select sector, count, amount
        from agg_sectors_to_cand
        where
            recipient_entity = %s
            and cycle = %s
        order by amount desc
        limit %s
    """


class TopPoliticiansByReceiptsHandler(TopListHandler):

    args = ['cycle', 'limit']

    fields = ['name', 'id', 'count', 'amount', 'state', 'party', 'seat']

    stmt = """
        select name, me.id, recipient_count, recipient_amount, state, party, seat
          from agg_entities ae
         inner join matchbox_entity me
            on ae.entity_id = id
         left join politician_metadata_latest_cycle_view pm
            on me.id = pm.entity_id
         where ae.cycle  = %s
           and type      = 'politician'
         order by recipient_amount desc, recipient_count desc
         limit %s
    """


class TopOrganizationsByContributionsHandler(TopListHandler):

    args = ['cycle', 'limit']

    fields = ['name', 'id', 'count', 'amount']

    stmt = """
        select name, id, contributor_count, contributor_amount
          from agg_entities
         inner join matchbox_entity
            on entity_id = id
         where cycle     = %s
           and type      = 'organization'
         order by contributor_amount desc, contributor_count desc
         limit %s
    """


class TopIndustriesByContributionsHandler(TopListHandler):

    args = ['cycle', 'limit']

    fields = ['name', 'id', 'count', 'amount', 'should_show_entity']

    stmt = """
        select name, me.id, contributor_count, contributor_amount, coalesce(should_show_entity, 't') as should_show_entity
          from agg_entities ae
         inner join matchbox_entity me
            on ae.entity_id = me.id
         left join matchbox_industrymetadata mim
            using (entity_id)
         where cycle = %s
           and type  = 'industry'
           and coalesce(should_show_entity, 't')
           and parent_industry_id is null -- don't include subindustries
         order by contributor_amount desc, contributor_count desc
         limit %s
    """

class TopIndustriesLifetimeHandler(TopListHandler):
    args = ['entity_id', 'cycle']
    fields = 'industry cycle amount'.split()

    stmt = """
        with industries_with_metadata as (
            select industry_entity, industry, recipient_entity, count, amount, name, parent_industry_id, cycle
            from agg_industries_to_cand ic
            inner join matchbox_entity me
                on me.id = ic.industry_entity
            left join matchbox_industrymetadata im
                on me.id = im.entity_id
            where
                type = 'industry'
                and coalesce(should_show_entity, 't')
                and parent_industry_id is null
                and recipient_entity = %s
                and cycle != -1
                and cycle >= %s
                and amount >= 0
        )
        select
            industry, cycle, coalesce(amount, 0) as amount
        from (

            select distinct industry_entity, industry, cycle
            from generate_series(
                (select min(cycle) from industries_with_metadata),
                (select max(cycle) from industries_with_metadata),
                2
            ) as cycles(cycle)
            cross join (
                select distinct industry_entity, industry from industries_with_metadata
            ) industries

        ) all_industries_and_cycles
        left join industries_with_metadata
            using (industry_entity, industry, cycle)
        order by
            industry, cycle, amount
    """

class TopIndividualsByContributionsHandler(TopListHandler):

    args = ['cycle', 'limit']

    fields = ['name', 'id', 'count', 'amount']

    stmt = """
        select name, id, contributor_count, contributor_amount
          from agg_entities
         inner join matchbox_entity
            on entity_id = id
         where cycle     = %s
           and type      = 'individual'
         order by contributor_amount desc, contributor_count desc
         limit %s
    """

class IndustryOrgHandler(EntityTopListHandler):
    fields = ['name', 'id', 'total_count', 'direct_count', 'employee_count', 'total_amount', 'direct_amount', 'employee_amount']

    stmt = """
        select organization_name, organization_entity, total_count, pacs_count, indivs_count, total_amount, pacs_amount, indivs_amount
        from agg_top_orgs_by_industry
        where
            industry_entity = %s
            and cycle = %s
        order by total_amount desc
        limit %s
    """


class ContributionAmountHandler(BaseHandler):

    args = ['contributor_entity', 'recipient_entity']

    fields = 'recipient_entity recipient_name contributor_entity contributor_name amount'.split()

    stmt = """
    select r.id, r.name, c.id, c.name,
        (select coalesce(sum(amount), 0)::integer
        from recipient_associations ra
        inner join (select * from contributor_associations union select * from organization_associations) ca
            on ca.entity_id = c.id
                and ra.entity_id = r.id
               and ca.transaction_id = ra.transaction_id
        inner join contributions_all_relevant contrib
            on contrib.transaction_id = ra.transaction_id
        %s) as amount
    from matchbox_entity r
    cross join matchbox_entity c
    where
        c.id = %%s
        and r.id = %%s
    """

    def read(self, request, **kwargs):
        cycle = request.GET.get('cycle', ALL_CYCLES)

        cache_key = self.get_cache_key('pairwise', kwargs['recipient_entity'], kwargs['contributor_entity'], cycle)
        cached = cache.get(cache_key, 'has expired')

        if cached == 'has expired':
            if cycle == ALL_CYCLES:
                cycle_where = ''
            else:
                cycle_where = 'where cycle = %d' % int(cycle)

            result = execute_one(self.stmt % cycle_where, *[kwargs[param] for param in self.args])

            if result:
                result = dict(zip(self.fields, result)) # add labels

            result = check_empty(result, kwargs['recipient_entity'], kwargs['contributor_entity'])
            cache.set(cache_key, result)

            return result
        else:
            return cached

    def get_cache_key(self, query_name, recipient_entity, contributor_entity, cycle):
        return "_".join([query_name, recipient_entity, contributor_entity, str(cycle)])

