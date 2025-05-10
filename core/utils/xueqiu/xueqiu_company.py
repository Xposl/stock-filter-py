from dataclasses import dataclass
from typing import Dict, Optional

@dataclass
class XueqiuZhCompany:
    """
    沪深公司详情
    """
    org_id: Optional[str]
    org_name_cn: Optional[str]
    org_short_name_cn: Optional[str]
    org_name_en: Optional[str]
    org_short_name_en: Optional[str]
    main_operation_business: Optional[str]
    operating_scope: Optional[str]
    district_encode: Optional[str]
    org_cn_introduction: Optional[str]
    legal_representative: Optional[str]
    general_manager: Optional[str]
    secretary: Optional[str]
    established_date: Optional[str]
    reg_asset: Optional[str]
    staff_num: Optional[str]
    telephone: Optional[str]
    postcode: Optional[str]
    fax: Optional[str]
    email: Optional[str]
    org_website: Optional[str]
    reg_address_cn: Optional[str]
    reg_address_en: Optional[str]
    office_address_cn: Optional[str]
    office_address_en: Optional[str]
    currency_encode: Optional[str]
    currency: Optional[str]
    listed_date: Optional[str]
    provincial_name: Optional[str]
    actual_controller: Optional[str]
    classi_name: Optional[str]
    pre_name_cn: Optional[str]
    chairman: Optional[str]
    executives_nums: Optional[str]
    actual_issue_vol: Optional[str]
    issue_price: Optional[str]
    actual_rc_net_amt: Optional[str]
    pe_after_issuing: Optional[str]
    online_success_rate_of_issue: Optional[str]

def xueqiu_zh_company_from_dict(data: Dict) -> XueqiuZhCompany:
    return XueqiuZhCompany(**data)

@dataclass
class XueqiuHkCompany:
    """
    港股公司详情
    """
    comunic: Optional[str]
    comcnname: Optional[str]
    comenname: Optional[str]
    incdate: Optional[str]
    rgiofc: Optional[str]
    hofclctmbu: Optional[str]
    chairman: Optional[str]
    mbu: Optional[str]
    comintr: Optional[str]
    refccomty: Optional[str]
    numtissh: Optional[str]
    ispr: Optional[str]
    nrfd: Optional[str]
    nation_name: Optional[str]
    tel: Optional[str]
    fax: Optional[str]
    email: Optional[str]
    web_site: Optional[str]
    lsdateipo: Optional[str]
    mainholder: Optional[str]

def xueqiu_hk_company_from_dict(data: Dict) -> XueqiuHkCompany:
    return XueqiuHkCompany(**data)

@dataclass
class XueqiuUsCompany:
    """
    美股公司详情
    """
    org_id: Optional[str]
    org_name_cn: Optional[str]
    org_short_name_cn: Optional[str]
    org_name_en: Optional[str]
    org_short_name_en: Optional[str]
    main_operation_business: Optional[str]
    operating_scope: Optional[str]
    district_encode: Optional[str]
    org_cn_introduction: Optional[str]
    legal_representative: Optional[str]
    general_manager: Optional[str]
    secretary: Optional[str]
    established_date: Optional[str]
    reg_asset: Optional[str]
    staff_num: Optional[str]
    telephone: Optional[str]
    postcode: Optional[str]
    fax: Optional[str]
    email: Optional[str]
    org_website: Optional[str]
    reg_address_cn: Optional[str]
    reg_address_en: Optional[str]
    office_address_cn: Optional[str]
    office_address_en: Optional[str]
    currency_encode: Optional[str]
    currency: Optional[str]
    listed_date: Optional[str]
    td_mkt: Optional[str]
    chairman: Optional[str]
    executives_nums: Optional[str]
    actual_issue_total_shares_num: Optional[str]
    actual_issue_price: Optional[str]
    total_raise_capital: Optional[str]
    mainholder: Optional[str]

def xueqiu_us_company_from_dict(data: Dict) -> XueqiuUsCompany:
    return XueqiuUsCompany(**data)
