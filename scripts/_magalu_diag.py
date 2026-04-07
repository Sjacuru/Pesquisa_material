from source_adapters.magalu_adapter import MagaluAdapter

adapter = MagaluAdapter()
result = adapter._search_selenium_fallback('cola bastao', timeout_seconds=45.0)
print('status=', result.status)
print('offers=', len(result.offers))
print('error=', result.error_message)
for i, offer in enumerate(result.offers[:5], start=1):
    print(i, offer.total_price, offer.product_title[:90], offer.product_url[:90])
