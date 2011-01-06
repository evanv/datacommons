from helpers import *

FPDS_FIELDS = [('unique_transaction_id','unique_transaction_id', None),
                ('transaction_status','transaction_status', None), # CAN'T FIND!!
                ('vendorname','vendorName', None),
                ('lastdatetoorder', None, None),
                ('agencyid', 'agencyid', splitCode),
                ('account_title', None, None),
                ('piid', 'PIID', None),
                ('modnumber', 'modNumber', None),
                ('vendordoingasbusinessname', 'vendorDoingAsBusinessName', None),
                ('transactionnumber', 'transactionNumber', None),
                ('idvagencyid', 'IDVAgencyID', None),
                ('idvpiid', 'IDVPIID', None),
                ('aiobflag', 'AIOBFlag', splitCode),
                ('idvmodificationnumber', 'IDVModificationNumber', None),
                ('signeddate', 'signedDate', None),
                ('effectivedate', 'effectiveDate', None),
                ('currentcompletiondate', 'currentCompletionDate', None),
                ('ultimatecompletiondate', 'ultimateCompletionDate', None),
                ('obligatedamount', 'obligatedAmount', float),
                ('shelteredworkshopflag', 'shelteredWorkshopFlag', transformFlag),
                ('baseandexercisedoptionsvalue', 'baseAndExercisedOptionsValue',  float),
                ('veteranownedflag', 'veteranOwnedFlag', transformFlag),
                ('srdvobflag', 'SRDVOBFlag', transformFlag),
                ('baseandalloptionsvalue', 'baseAndAllOptionsValue', float),
                ('contractingofficeagencyid', 'contractingOfficeAgencyID', splitCode),
                ('womenownedflag', 'womenOwnedFlag', transformFlag),
                ('contractingofficeid', 'contractingOfficeID', None),
                ('minorityownedbusinessflag', 'minorityOwnedBusinessFlag', transformFlag),
                ('fundingrequestingagencyid', 'fundingRequestingAgencyID', splitCode),
                ('saaobflag', 'SAAOBFlag', transformFlag),
                ('apaobflag', 'APAOBFlag', transformFlag),
                ('fundingrequestingofficeid', 'fundingRequestingOfficeID', None),
                ('purchasereason', 'purchaseReason', splitCode),
                ('baobflag', 'BAOBFlag', transformFlag),
                ('fundedbyforeignentity', 'fundedByForeignEntity', splitCode),
                ('haobflag', 'HAOBFlag', transformFlag),
                ('naobflag', 'NAOBFlag', transformFlag),
                ('contractactiontype', 'contractActionType', splitCode),
                ('typeofcontractpricing', 'typeOfContractPricing', splitCode),
                ('verysmallbusinessflag', 'verySmallBusinessFlag', transformFlag),
                ('reasonformodification', 'reasonForModification', splitCode),
                ('federalgovernmentflag', 'federalGovernmentFlag', transformFlag),
                ('majorprogramcode', 'majorProgramCode', None),
                ('costorpricingdata', 'costOrPricingData', None),
                ('solicitationid', 'solicitationID', None),
                ('costaccountingstandardsclause', 'costAccountingStandardsClause', splitCode),
                ('stategovernmentflag', 'stateGovernmentFlag', transformFlag),
                ('descriptionofcontractrequirement', 'descriptionOfContractRequirement', None),
                ('localgovernmentflag', 'localGovernmentFlag', transformFlag),
                ('gfe_gfp', 'GFE_GFP', transformFlag),
                ('seatransportation', 'seaTransportation', transformFlag), # this data is weird, doesn't match other flags--don't really know how to parse 
                ('consolidatedcontract', 'consolidatedContract', transformFlag),
                ('lettercontract', 'letterContract', splitCode),
                ('multiyearcontract', 'multiYearContract', transformFlag),
                ('performancebasedservicecontract', 'performanceBasedServiceContract', splitCode),
                ('contingencyhumanitarianpeacekeepingoperation', 'contingencyHumanitarianPeacekeepingOperation', splitCode),
                ('tribalgovernmentflag', 'tribalGovernmentFlag', transformFlag),
                ('contractfinancing', 'contractFinancing', splitCode),
                ('purchasecardaspaymentmethod', 'purchaseCardAsPaymentMethod', transformFlag),
                ('numberofactions', 'numberOfActions', int),
                ('walshhealyact', 'WalshHealyAct', transformFlag),
                ('servicecontractact', 'serviceContractAct', transformFlag),
                ('davisbaconact', 'DavisBaconAct', transformFlag),
                ('clingercohenact', 'ClingerCohenAct', transformFlag),
                ('interagencycontractingauthority', 'interagencyContractingAuthority', splitCode),
                ('productorservicecode', 'productOrServiceCode', splitCode),
                ('contractbundling', 'contractBundling', splitCode),
                ('claimantprogramcode', 'claimantProgramCode', splitCode),
                ('principalnaicscode', 'principalNAICSCode', splitCode),
                ('recoveredmaterialclauses', 'recoveredMaterialClauses', splitCode),
                ('educationalinstitutionflag', 'educationalInstitutionFlag', transformFlag),
                ('systemequipmentcode', 'systemEquipmentCode', splitCode),
                ('hospitalflag', 'hospitalFlag', transformFlag),
                ('informationtechnologycommercialitemcategory', 'informationTechnologyCommercialItemCategory', splitCode),
                ('useofepadesignatedproducts', 'useOfEPADesignatedProducts', splitCode),
                ('countryoforigin', 'countryOfOrigin', splitCode),
                ('placeofmanufacture', 'placeOfManufacture', splitCode),
                ('streetaddress', 'streetAddress', None),
                ('streetaddress2', 'streetAddress2', None),
                ('streetaddress3', 'streetAddress3', None),
                ('city', 'city', None),
                ('state', 'state', splitCode),
                ('zipcode', 'ZIPCode', None),
                ('vendorcountrycode', 'vendorCountryCode', None),
                ('dunsnumber', 'DUNSNumber', None),
                ('congressionaldistrict', 'congressionalDistrict', None),
                ('locationcode', 'locationCode', None),
                ('statecode', 'stateCode', splitCode),
                ('placeofperformancecountrycode', 'placeOfPerformanceCountryCode', splitCode),
                ('placeofperformancezipcode', 'placeOfPerformanceZIPCode', None),
                ('nonprofitorganizationflag', 'nonprofitOrganizationFlag', transformFlag),
                ('placeofperformancecongressionaldistrict', 'placeofperformancecongressionaldistrict', None),
                ('extentcompeted', 'extentcompeted', splitCode),
                ('competitiveprocedures', 'competitiveprocedures', splitCode),
                ('solicitationprocedures', 'solicitationProcedures', splitCode),
                ('typeofsetaside', 'typeOfSetAside', splitCode),
                ('organizationaltype', 'organizationalType', None),
                ('evaluatedpreference', 'evaluatedPreference', splitCode),
                ('numberofemployees', 'numberOfEmployees', int),
                ('research', 'research', splitCode),
                ('annualrevenue', 'annualRevenue', float),
                ('statutoryexceptiontofairopportunity', 'statutoryExceptionToFairOpportunity', splitCode),
                ('reasonnotcompeted', 'reasonNotCompeted', splitCode),
                ('numberofoffersreceived', 'numberOfOffersReceived', int),
                ('commercialitemacquisitionprocedures', 'commercialItemAcquisitionProcedures', splitCode),
                ('hbcuflag', 'HBCUFlag', transformFlag),
                ('commercialitemtestprogram', 'commercialItemTestProgram', transformFlag),
                ('smallbusinesscompetitivenessdemonstrationprogram', 'smallBusinessCompetitivenessDemonstrationProgram', transformFlag),
                ('a76action', 'A76Action', transformFlag),
                ('sdbflag', 'SDBFlag', transformFlag),
                ('firm8aflag', 'firm8AFlag', transformFlag),
                ('hubzoneflag', 'HUBZoneFlag', transformFlag),
                ('phoneno', 'phoneNo', None),
                ('faxno', 'faxNo', None),
                ('contractingofficerbusinesssizedetermination', 'contractingOfficerBusinessSizeDetermination', splitCode),
                ('otherstatutoryauthority', 'otherStatutoryAuthority', None),
                ('eeparentduns', 'eeParentDuns', None),
                ('fiscal_year', 'fiscal_year', int),
                ('mod_parent', 'mod_parent', None),
                ('maj_agency_cat', 'maj_agency_cat', splitCode),
                ('psc_cat', 'psc_cat', splitCode),
                ('vendor_cd', 'vendor_cd', splitCode),
                ('pop_cd', 'pop_cd', splitCode),
                ('progsourceagency', 'ProgSourceAgency', splitCode),
                ('progsourceaccount', 'ProgSourceAccount', splitCode),
                ('progsourcesubacct', 'ProgSourceSubAcct', splitCode),
                ('rec_flag', 'rec_flag', transformFlag),
                ('type_of_contract', 'type_of_contract', splitCode)]





        
    
    
    
