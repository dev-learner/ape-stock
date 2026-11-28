# scripts/populate_missing_descriptions.py
# NAME: Populate Missing Descriptions
# DESC: Inserts short business descriptions for the symbols that yfinance could not cover.
# DETAIL: Uses a hard-coded dictionary of the previously missing FTSE 100/250 names (mostly investment trusts and specialist vehicles). Creates the table if needed. Safe to re-run (INSERT OR REPLACE).
# ALLOW_DELETE: 1
# RUN: Tool2
# CATEGORY: data

"""
Populate Missing Descriptions
-----------------------------
Fills the gaps left by the yfinance fetch.
"""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "ape_stock.db"

MISSING = {
    "3IN.L": "3i Infrastructure is an investment trust focused on infrastructure assets in Europe and North America. It aims to deliver long-term returns through investments in essential infrastructure sectors.",
    "AAS.L": "Aberforth Smaller Companies Trust invests in a diversified portfolio of smaller UK companies. It seeks capital growth through a value-oriented approach to UK small-cap equities.",
    "AGT.L": "AVI Global Trust is an investment trust that holds a portfolio of global equities, with a focus on undervalued companies and special situations.",
    "AIE.L": "Ashoka India Equity Investment Trust focuses on Indian equities, seeking long-term capital growth through a concentrated portfolio of high-quality Indian companies.",
    "ALW.L": "Alliance Witan is a global equity investment trust. It aims for capital growth by investing in a diversified portfolio of international companies.",
    "ASL.L": "Aberforth Split Level Income Trust provides income and capital growth through investment in smaller UK companies, with a split capital structure.",
    "ATR.L": "Schroder Asian Total Return Investment Company invests in Asian equities with the aim of delivering total returns through a combination of capital growth and income.",
    "ATT.L": "Allianz Technology Trust focuses on global technology companies, seeking capital growth through investment in leading and emerging technology stocks.",
    "BBOX.L": "Tritax Big Box REIT owns and manages a portfolio of large-scale logistics warehouses in the UK, leased to major retailers and third-party logistics providers.",
    "BGFD.L": "Baillie Gifford Japan Trust invests in Japanese equities, focusing on companies with strong growth potential.",
    "BHMG.L": "BH Macro is a feeder fund that invests in the Brevan Howard Master Fund, a multi-strategy hedge fund.",
    "BPCR.L": "BioPharma Credit invests in debt instruments issued by life sciences companies, providing income through royalty and debt financing.",
    "BRGE.L": "BlackRock Greater Europe Investment Trust focuses on European equities, seeking capital growth through a concentrated portfolio.",
    "BRSC.L": "BlackRock Smaller Companies Trust invests in smaller UK companies with the aim of achieving capital growth.",
    "BRWM.L": "BlackRock World Mining Trust invests in mining and metals companies globally, seeking capital growth and income.",
    "BUT.L": "Brunner Investment Trust is a global equity trust that aims for long-term capital and income growth through a diversified portfolio.",
    "CGT.L": "Capital Gearing Trust is a multi-asset investment trust focused on capital preservation and real returns, with a conservative allocation.",
    "CLDN.L": "Caledonia Investments is a self-managed investment trust with a portfolio of quoted and unquoted investments, including significant family-controlled holdings.",
    "CORD.L": "Cordiant Digital Infrastructure invests in digital infrastructure assets such as data centres, mobile towers and fibre networks.",
    "CTY.L": "City of London Investment Trust is a long-established UK equity income trust that aims to provide income and capital growth.",
    "EDIN.L": "Edinburgh Investment Trust focuses on UK equities with the objective of providing income and capital growth.",
    "ESCT.L": "European Smaller Companies Trust invests in smaller companies across Europe, seeking capital growth.",
    "EWI.L": "Edinburgh Worldwide Investment Trust focuses on global smaller companies with high growth potential, particularly in technology and innovation.",
    "FCIT.L": "F&C Investment Trust is one of the oldest investment trusts, holding a diversified global equity portfolio for capital growth.",
    "FCSS.L": "Fidelity China Special Situations invests in Chinese equities, including both onshore and offshore listings.",
    "FEML.L": "Fidelity Emerging Markets Limited focuses on emerging market equities for long-term capital growth.",
    "FEV.L": "Fidelity European Trust invests in European equities, seeking capital growth through a diversified portfolio.",
    "FGEN.L": "Foresight Environmental Infrastructure invests in environmental infrastructure assets, primarily in the UK and Europe.",
    "FGT.L": "Finsbury Growth & Income Trust is a concentrated UK equity portfolio focused on high-quality growth companies.",
    "FSV.L": "Fidelity Special Values invests in UK equities with a value-oriented approach, seeking capital growth.",
    "GCP.L": "GCP Infrastructure Investments focuses on UK infrastructure debt, providing income through secured lending to infrastructure projects.",
    "GROW.L": "Molten Ventures is a venture capital investor focused on high-growth technology companies, primarily in Europe.",
    "GSCT.L": "Goldman Sachs Global Strategic Equity Trust invests in a concentrated portfolio of global equities.",
    "HAN.L": "Hansa Investment Company is an investment trust with a portfolio of equities and other assets, managed with a long-term approach.",
    "HFEL.L": "Henderson Far East Income invests in Asian equities with a focus on income generation.",
    "HGT.L": "HgCapital Trust is a private equity trust focused on software and technology investments in Europe and North America.",
    "HICL.L": "HICL Infrastructure is an investment company that owns a portfolio of infrastructure assets, primarily in the UK.",
    "HRI.L": "Herald Investment Trust focuses on smaller quoted companies in the technology, media and telecommunications sectors.",
    "HSL.L": "Henderson Smaller Companies Investment Trust invests in smaller UK companies for capital growth.",
    "HVPE.L": "HarbourVest Global Private Equity is a fund of funds investing in private equity funds globally.",
    "IAD.L": "Invesco Asia Trust focuses on Asian equities, seeking capital growth through investment in the region.",
    "ICGT.L": "ICG Enterprise Trust is a private equity investment trust that invests in mid-market buyouts, primarily in Europe and the US.",
    "INPP.L": "International Public Partnerships invests in infrastructure assets, primarily in the UK and internationally.",
    "JAM.L": "JPMorgan American Investment Trust focuses on US equities for capital growth.",
    "JCH.L": "JPMorgan Claverhouse Investment Trust invests in UK equities with an income and growth objective.",
    "JEDT.L": "JPMorgan European Discovery Trust focuses on European smaller companies.",
    "JEGI.L": "JPMorgan European Growth & Income invests in European equities with a focus on income and growth.",
    "JEMI.L": "JPMorgan Emerging Markets Investment Trust focuses on emerging market equities.",
    "JGGI.L": "JPMorgan Global Growth & Income invests in a global equity portfolio with an income focus.",
    "JMGI.L": "JPMorgan Global Core Real Assets invests in real assets including infrastructure, real estate and transportation.",
    "LWDB.L": "Law Debenture is an investment trust with a diversified equity portfolio and a professional services business.",
    "MNKS.L": "Monks Investment Trust is a global equity trust managed with a growth-oriented approach.",
    "MNTN.L": "Montanaro European Smaller Companies Trust focuses on smaller European companies.",
    "MRC.L": "Mercantile Investment Trust invests in UK smaller and mid-sized companies.",
    "MRCH.L": "Merchants Trust is a UK equity income trust focused on higher-yielding companies.",
    "MUT.L": "Murray Income Trust invests in UK equities with the aim of providing income and capital growth.",
    "MYI.L": "Murray International Trust holds a global equity portfolio with a focus on income.",
    "NAIT.L": "North American Income Trust focuses on North American equities for income and capital growth.",
    "NAS.L": "North Atlantic Smaller Companies Investment Trust invests in smaller companies in the UK, US and Europe.",
    "NBPE.L": "NB Private Equity Partners is a private equity investment company focused on direct co-investments.",
    "OCI.L": "Oakley Capital Investments is a private equity investment trust focused on mid-market European companies.",
    "PCGH.L": "Polar Capital Global Healthcare Trust invests in global healthcare equities.",
    "PCT.L": "Polar Capital Technology Trust focuses on global technology companies.",
    "PEY.L": "Petershill Partners is an investment company that provides capital to alternative asset managers.",
    "PHI.L": "Pacific Horizon Investment Trust focuses on Asia-Pacific equities, particularly growth companies.",
    "PIN.L": "Pantheon International is a private equity fund of funds with a global portfolio.",
    "PINT.L": "Polar Capital Global Financials Trust invests in financial services companies worldwide.",
    "PNL.L": "Personal Assets Trust is a multi-asset investment trust focused on capital preservation.",
    "PPET.L": "Patria Private Equity Trust invests in private equity funds, primarily in Europe.",
    "PSH.L": "Pershing Square Holdings is a concentrated investment trust managed by Bill Ackman’s firm, focused on large-cap equities.",
    "RCP.L": "RIT Capital Partners is a multi-asset investment trust with a global portfolio of equities, private investments and other assets.",
    "RICA.L": "Ruffer Investment Company is a multi-asset trust focused on capital preservation and absolute returns.",
    "RTW.L": "RTW Biotech Opportunities invests in biotechnology and life sciences companies.",
    "SAIN.L": "Scottish American Investment Company focuses on global equities with an income objective.",
    "SDP.L": "Schroder UK Mid Cap Fund invests in UK mid-sized companies.",
    "SEIT.L": "SDCL Energy Efficiency Income Trust invests in energy efficiency and distributed energy projects.",
    "SEQI.L": "Sequoia Economic Infrastructure Income Fund invests in economic infrastructure debt.",
    "SMT.L": "Scottish Mortgage Investment Trust is a global equity trust with a focus on high-growth companies, including technology and innovation.",
    "SOI.L": "Schroder Oriental Income Fund focuses on Asian equities for income.",
    "SSIT.L": "Seraphim Space Investment Trust focuses on space technology companies.",
    "SYNC.L": "Syncona is a life sciences investment company focused on founding and building healthcare businesses.",
    "TEM.L": "Templeton Emerging Markets Investment Trust focuses on emerging market equities.",
    "TFIF.L": "TwentyFour Income Fund invests in European asset-backed securities for income.",
    "THRL.L": "Target Healthcare REIT owns a portfolio of UK care homes.",
    "TMPL.L": "Temple Bar Investment Trust is a UK equity income trust with a value approach.",
    "TRIG.L": "The Renewables Infrastructure Group invests in renewable energy infrastructure assets, primarily wind and solar.",
    "TRY.L": "TR Property Investment Trust focuses on property companies and real estate securities in Europe.",
    "UKW.L": "Greencoat UK Wind owns a portfolio of UK wind farms.",
    "USA.L": "Baillie Gifford US Growth Trust focuses on US growth equities.",
    "VOF.L": "VinaCapital Vietnam Opportunity Fund invests in Vietnamese equities and private companies.",
}

def main():
    conn = sqlite3.connect(DB_PATH, timeout=60)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS company_descriptions (
            symbol TEXT PRIMARY KEY,
            description TEXT,
            updated_at TEXT DEFAULT (datetime('now'))
        )
    """)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    count = 0

    for symbol, desc in MISSING.items():
        cur.execute("""
            INSERT OR REPLACE INTO company_descriptions (symbol, description, updated_at)
            VALUES (?, ?, ?)
        """, (symbol, desc, now))
        count += 1

    conn.commit()
    conn.close()
    print(f"Inserted/updated {count} missing descriptions.")

if __name__ == "__main__":
    main()