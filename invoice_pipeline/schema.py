from pydantic import BaseModel, Field


class VatLine(BaseModel):
    base: float = Field(description="Taxable base in EUR for this VAT rate")
    vat_rate: float = Field(description="VAT percentage, e.g. 21, 10, 4, 0")
    vat_amount: float = Field(description="VAT amount (cuota) in EUR")
    surcharge_rate: float = Field(0.0, description="Recargo de equivalencia percentage, 0 if none")
    surcharge_amount: float = Field(0.0, description="Recargo de equivalencia amount in EUR, 0 if none")


class Invoice(BaseModel):
    issuer_name: str
    issuer_nif: str = Field(description="Supplier NIF/CIF exactly as printed")
    recipient_nif: str = Field("", description="Customer NIF/CIF exactly as printed, empty if absent")
    invoice_number: str
    issue_date: str = Field(description="ISO date YYYY-MM-DD")
    concept: str = Field(description="Short description of what was bought")
    vat_lines: list[VatLine]
    withholding_rate: float = Field(0.0, description="IRPF retention percentage, 0 if none")
    withholding_amount: float = Field(0.0, description="IRPF retention amount in EUR, 0 if none")
    total: float = Field(description="Total amount payable in EUR")
    suggested_expense_account: str = Field(
        description="Suggested Spanish PGC expense account (e.g. 628 suministros, 629 otros servicios, 600 compras)")
