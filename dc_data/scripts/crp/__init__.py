"""
Scripts needed to turn raw data from CRP and NIMSP into a SQL database usable by Data Commons applications.
(Note: these scripts generate transactional data in CRP format. Just for use in the prototype.
The denormalize scripts generate the real Contribution tables.)

Very rough instructions:
1. run crp_csv2sql.py to turn CRP individual_contributions data into SQL insert statements.
2. load the resulting file into a MySQL database.
3. run normalize_crp.py to create the normalization table.
4. run build_crp_entities.py to create the entities table.

"""