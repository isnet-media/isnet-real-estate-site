"""Build TLV comparison data with the existing shared fixed-quantity builders."""
from refresh_tlv_super_prices import SITE,validate
from super_city_runtime import load
def build():
 validate(SITE/'data')
 load('build_super_city_basket','TLV').build()
 load('build_super_smart_shopping','TLV').build()
 validate(SITE/'data')
if __name__=='__main__':build()
