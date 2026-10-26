import unittest
from varasto import Varasto


class TestVarasto(unittest.TestCase):
    def setUp(self):
        self.varasto = Varasto(10)
        self.negvarasto = Varasto(-1, -1)
        self.hukkavarasto = Varasto(1, 2)

    def test_konstruktori_luo_tyhjan_varaston(self):
        # https://docs.python.org/3/library/unittest.html#unittest.TestCase.assertAlmostEqual
        self.assertAlmostEqual(self.varasto.saldo, 0)

    def test_uudella_varastolla_oikea_tilavuus(self):
        self.assertAlmostEqual(self.varasto.tilavuus, 10)

    def test_uuden_varaston_tilavuus_nolla_negatiivisella_aloitusarvolla(self):
        self.assertAlmostEqual(self.negvarasto.tilavuus, 0)

    def test_uuden_varaston_saldo_nolla_negatiivisella_aloitusarvolla(self):
        self.assertAlmostEqual(self.negvarasto.saldo, 0)

    def test_uuden_varaston_saldo_ei_voi_olla_suurempi_kuin_tilavuus(self):
        self.assertAlmostEqual(self.hukkavarasto.saldo, self.hukkavarasto.tilavuus)

    def test_lisays_ei_voi_olla_negatiivinen(self):
        self.varasto.lisaa_varastoon(8)
        self.assertAlmostEqual(self.varasto.saldo, 8)

        self.varasto.lisaa_varastoon(-1)
        self.assertAlmostEqual(self.varasto.saldo, 8)

    def test_saldo_lisayksen_jalkeen_ei_voi_olla_suurempi_kuin_tilavuus(self):
        self.assertAlmostEqual(self.varasto.tilavuus, 10)
        self.varasto.lisaa_varastoon(20)
        self.assertAlmostEqual(self.varasto.saldo, self.varasto.tilavuus)

    def test_lisays_lisaa_saldoa(self):
        self.varasto.lisaa_varastoon(8)

        self.assertAlmostEqual(self.varasto.saldo, 8)

    def test_lisays_lisaa_pienentaa_vapaata_tilaa(self):
        self.varasto.lisaa_varastoon(8)

        # vapaata tilaa pitäisi vielä olla tilavuus-lisättävä määrä eli 2
        self.assertAlmostEqual(self.varasto.paljonko_mahtuu(), 2)

    def test_otto_ei_voi_olla_negatiivinen(self):
        self.varasto.lisaa_varastoon(8)
        self.assertAlmostEqual(self.varasto.saldo, 8)

        saatu_maara = self.varasto.ota_varastosta(-1)
        self.assertAlmostEqual(self.varasto.saldo, 8)
        self.assertAlmostEqual(saatu_maara, 0)

    def test_ei_voi_ottaa_saldoa_enempaa(self):
        self.varasto.lisaa_varastoon(8)
        self.assertAlmostEqual(self.varasto.saldo, 8)

        saatu_maara = self.varasto.ota_varastosta(10)
        self.assertAlmostEqual(self.varasto.saldo, 0)
        self.assertAlmostEqual(saatu_maara, 8)

    def test_ottaminen_palauttaa_oikean_maaran(self):
        self.varasto.lisaa_varastoon(8)

        saatu_maara = self.varasto.ota_varastosta(2)

        self.assertAlmostEqual(saatu_maara, 2)

    def test_ottaminen_lisaa_tilaa(self):
        self.varasto.lisaa_varastoon(8)

        self.varasto.ota_varastosta(2)

        # varastossa pitäisi olla tilaa 10 - 8 + 2 eli 4
        self.assertAlmostEqual(self.varasto.paljonko_mahtuu(), 4)

    def test_tuloste(self):
        self.varasto.lisaa_varastoon(1)
        self.assertEqual(str(self.varasto), "saldo = 1, vielä tilaa 9")
