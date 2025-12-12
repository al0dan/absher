from lxml import etree
import uuid
from datetime import datetime

class ZatcaService:
    def generate_invoice_xml(self, contract):
        """
        Generates a simplified ZATCA-compliant UBL 2.1 Invoice XML.
        Note: Real production ZATCA requires cryptographic signing (CSID),
        QR code TLV generation, and hash chains. This generates the 
        STANDARD XML STRUCTURE.
        """
        
        # Namespaces
        nsmap = {
            None: "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2",
            "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
            "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
            "ext": "urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2"
        }
        
        invoice = etree.Element("Invoice", nsmap=nsmap)
        
        # Basic Header
        self._add_cbc(invoice, "ProfileID", "reporting:1.0")
        self._add_cbc(invoice, "ID", contract['id'])
        self._add_cbc(invoice, "UUID", str(uuid.uuid4()))
        self._add_cbc(invoice, "IssueDate", datetime.now().strftime("%Y-%m-%d"))
        self._add_cbc(invoice, "IssueTime", datetime.now().strftime("%H:%M:%S"))
        self._add_cbc(invoice, "InvoiceTypeCode", "388", name="0100000") # Tax Invoice
        self._add_cbc(invoice, "DocumentCurrencyCode", "SAR")
        self._add_cbc(invoice, "TaxCurrencyCode", "SAR")
        
        # Supplier
        supplier_party = etree.SubElement(invoice, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}AccountingSupplierParty")
        party = etree.SubElement(supplier_party, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}Party")
        party_name = etree.SubElement(party, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}PartyName")
        self._add_cbc(party_name, "Name", contract['supplier'])
        
        party_tax = etree.SubElement(party, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}PartyTaxScheme")
        self._add_cbc(party_tax, "CompanyID", contract['supplier_vat'] or '300000000000003')
        tax_scheme = etree.SubElement(party_tax, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}TaxScheme")
        self._add_cbc(tax_scheme, "ID", "VAT")
        
        # Customer
        cust_party = etree.SubElement(invoice, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}AccountingCustomerParty")
        c_party = etree.SubElement(cust_party, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}Party")
        c_name = etree.SubElement(c_party, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}PartyName")
        self._add_cbc(c_name, "Name", contract['buyer'])
        
        # Totals
        price = contract['price']
        vat_rate = 0.15
        vat_amount = price * vat_rate
        total_amount = price + vat_amount
        
        tax_total = etree.SubElement(invoice, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}TaxTotal")
        self._add_ebc(tax_total, "TaxAmount", f"{vat_amount:.2f}", "SAR")
        
        legal_monetary_total = etree.SubElement(invoice, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}LegalMonetaryTotal")
        self._add_ebc(legal_monetary_total, "LineExtensionAmount", f"{price:.2f}", "SAR")
        self._add_ebc(legal_monetary_total, "TaxExclusiveAmount", f"{price:.2f}", "SAR")
        self._add_ebc(legal_monetary_total, "TaxInclusiveAmount", f"{total_amount:.2f}", "SAR")
        self._add_ebc(legal_monetary_total, "PayableAmount", f"{total_amount:.2f}", "SAR")
        
        # Line Item
        line = etree.SubElement(invoice, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}InvoiceLine")
        self._add_cbc(line, "ID", "1")
        self._add_ebc(line, "InvoicedQuantity", "1", "UNIT")
        self._add_ebc(line, "LineExtensionAmount", f"{price:.2f}", "SAR")
        
        item = etree.SubElement(line, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}Item")
        self._add_cbc(item, "Name", contract['items'][:50]) # Truncate checks
        
        price_component = etree.SubElement(line, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}Price")
        self._add_ebc(price_component, "PriceAmount", f"{price:.2f}", "SAR")

        return etree.tostring(invoice, pretty_print=True, xml_declaration=True, encoding="UTF-8")

    def _add_cbc(self, parent, tag, text, **attribs):
        elem = etree.SubElement(parent, f"{{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}}{tag}", **attribs)
        elem.text = str(text)
        
    def _add_ebc(self, parent, tag, text, currency):
         elem = etree.SubElement(parent, f"{{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}}{tag}", currencyID=currency)
         elem.text = str(text)
