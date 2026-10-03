import pathlib, re, unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
class TestPackage(unittest.TestCase):
    def test_required_files(self):
        for p in ['SKILL.md','README.md','CHANGELOG.md','MANUAL_ACTIVATION.md','ACTIVATION_SMOKE_TEST.md','agents/openai.yaml','references/qa-checklist.md','references/audit-rubric.md','references/google-sheets-mobile-capabilities.md','scripts/bump_version.py']:
            self.assertTrue((ROOT/p).exists(), p)
    def test_core_rules(self):
        s=(ROOT/'SKILL.md').read_text()
        for phrase in ['Single editable source of truth','Blank is not zero','Primary action first','NATIVE GOOGLE SHEETS — UNVERIFIED','ACT → ORIENT → CHECK → NAVIGATE → ANALYZE → ADMINISTER']:
            self.assertIn(phrase,s)
    def test_scope_and_device_class_gate(self):
        s=(ROOT/'SKILL.md').read_text()
        for phrase in ['BUILD','AUDIT_REPAIR_REAUDIT','MOBILE-PRIMARY','MOBILE-SECONDARY','DESKTOP-PRIMARY','Do not confuse BUILD with REPAIR']:
            self.assertIn(phrase,s)
    def test_native_conversion_v120_gates(self):
        s=(ROOT/'SKILL.md').read_text()
        for phrase in ['operating timezone','merged ranges','conditional-format','successful API/tool response','SOURCE VALIDATED → CONVERTED → NATIVE AUDITED → NATIVE REPAIRED → RE-AUDITED → MOBILE VERIFIED','MOBILE VERIFIED']:
            self.assertIn(phrase,s)
        q=(ROOT/'references'/'qa-checklist.md').read_text()
        for phrase in ['Intended operating timezone','Merged ranges inspected','Material native mutations','Navigation tested as a working action']:
            self.assertIn(phrase,q)
    def test_no_hospital_specific_dependency(self):
        s=(ROOT/'SKILL.md').read_text().lower()
        for phrase in ['male ward','female ward','dengue','measles','diarrhoea']:
            self.assertNotIn(phrase,s)

    def test_all_current_version_mirrors_are_121(self):
        import json
        files = {
            'SKILL.md': re.search(r'^version:\s*([^\s]+)', (ROOT/'SKILL.md').read_text(), re.M).group(1),
            'README.md': re.search(r'v(\d+\.\d+\.\d+)', (ROOT/'README.md').read_text()).group(1),
            'CHANGELOG.md': re.search(r'^## \[([^\]]+)\]', (ROOT/'CHANGELOG.md').read_text(), re.M).group(1),
            'MANUAL_ACTIVATION.md': re.search(r'v(\d+\.\d+\.\d+)', (ROOT/'MANUAL_ACTIVATION.md').read_text()).group(1),
            'ACTIVATION_SMOKE_TEST.md': re.search(r'- version:\s*(\d+\.\d+\.\d+)', (ROOT/'ACTIVATION_SMOKE_TEST.md').read_text()).group(1),
            'agents/openai.yaml': re.search(r'^version:\s*([^\s]+)', (ROOT/'agents'/'openai.yaml').read_text(), re.M).group(1),
            'PACKAGE_MANIFEST.json': json.loads((ROOT/'PACKAGE_MANIFEST.json').read_text())['version'],
        }
        self.assertEqual(set(files.values()), {'1.2.1'}, files)

    def test_top_level_sections_are_sequential_and_unique(self):
        s=(ROOT/'SKILL.md').read_text()
        nums=[int(n) for n in re.findall(r'^##\s+(\d+)\.', s, re.M)]
        self.assertEqual(nums, list(range(1, len(nums)+1)))

if __name__=='__main__': unittest.main()