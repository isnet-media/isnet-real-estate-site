"""Do not confuse a successful packaging step with verified public-site readiness."""
from pathlib import Path
from tempfile import TemporaryDirectory
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"scripts"))
from audit_super_independent_site import ResourceParser, audit_city, classify_url

class SiteReadinessSafety(unittest.TestCase):
    def test_url_within_city(self):
        self.assertEqual(classify_url("YAVNE","index.html","/SUPER.YAVNE/assets/site.css"),("local","assets/site.css"))
        self.assertEqual(classify_url("YAVNE","recipes/index.html","../assets/design-system.css"),("local","assets/design-system.css"))
    def test_block_traversal_and_unknown_root(self):
        self.assertEqual(classify_url("YAVNE","index.html","../../secret"),("escapes_city","../../secret"))
        self.assertEqual(classify_url("YAVNE","index.html","/SUPER.RISHON/data/prices.json")[0],"origin_route_unverified")
    def test_external_not_considered_local(self):
        self.assertEqual(classify_url("YAVNE","index.html","https://media.example.com/a.webp")[0],"external")
        self.assertEqual(classify_url("YAVNE","index.html","//cdn.example.com/app.js")[0],"external")
    def test_extract_html_resources(self):
        p=ResourceParser()
        p.feed('<img src="assets/a.webp"><link href="/SUPER.YAVNE/a.css" rel="stylesheet"><style>.x{background:url("assets/b.webp")}</style>')
        self.assertEqual(len(p.resources),3)
    def test_canonical_is_not_an_external_static_asset(self):
        p=ResourceParser()
        p.feed('<link rel="canonical" href="https://isnet.co.il/SUPER.YAVNE/">')
        self.assertEqual(p.resources,[])
        self.assertEqual(p.canonicals,["https://isnet.co.il/SUPER.YAVNE/"])

    def test_generator_template_is_not_a_served_html_page(self):
        with TemporaryDirectory() as d:
            root=Path(d)
            (root/"SUPER.YAVNE"/"assets"/"branding").mkdir(parents=True)
            (root/"SUPER.YAVNE"/"index.html").write_text('<h1>Yavne</h1>',encoding="utf-8")
            (root/"SUPER.YAVNE"/"assets"/"branding"/"super-shell.html").write_text('<img src="{{ROOT}}no.png">',encoding="utf-8")
            result=audit_city(root,"YAVNE")
            self.assertEqual(result["missing_local_static_resources"],[])

    def test_ordinary_js_navigation_is_not_an_index_meta_redirect(self):
        with TemporaryDirectory() as d:
            root=Path(d)
            (root/"SUPER.YAVNE").mkdir()
            (root/"SUPER.YAVNE"/"index.html").write_text('<script>window.location.href="#search"</script>',encoding="utf-8")
            result=audit_city(root,"YAVNE")
            self.assertFalse(result["meta_or_script_redirect_index"])

    def test_missing_asset_blocks_public_acceptance(self):
        with TemporaryDirectory() as d:
            root=Path(d)
            (root/"SUPER.YAVNE").mkdir()
            (root/"SUPER.YAVNE"/"index.html").write_text('<img src="missing.webp">',encoding="utf-8")
            c=audit_city(root,"YAVNE")
            self.assertEqual(c["missing_local_static_resources"],[["index.html","missing.webp"]])
            self.assertFalse(c["public_cutover_approved"])
    def test_tlv_placeholder_and_license_not_assumed(self):
        with TemporaryDirectory() as d:
            root=Path(d)
            (root/"SUPER.TLV").mkdir()
            (root/"SUPER.TLV"/"index.html").write_text('<meta http-equiv="refresh" content="0;url=/">',encoding="utf-8")
            c=audit_city(root,"TLV")
            self.assertTrue(c["meta_or_script_redirect_index"])
            self.assertFalse(c["media_rights_verified"])
            self.assertFalse(c["production_rollback_verified"])
if __name__ == "__main__": unittest.main()
