Write-Host "Compiling orders_example.l to ClickHouse SQL..." -ForegroundColor Cyan
Write-Host ""

$body = @{
    program = 'HighValueSales(order_id:, amount:) :- `warehouse.sales_data.fact_orders`(order_id:, amount:, region: "US-West"), amount > 5000;'
    predicate = "HighValueSales"
    dialect = "clickhouse"
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "http://localhost:5000/api/Logica/compile" -Method Post -Body $body -ContentType "application/json"

    if ($response.success) {
        Write-Host "Dialect: $($response.dialect)" -ForegroundColor Green
        Write-Host ""
        Write-Host "Generated SQL:" -ForegroundColor Green
        Write-Host $response.sql
    } else {
        Write-Host "Error: $($response.error)" -ForegroundColor Red
    }
} catch {
    Write-Host "Request failed: $_" -ForegroundColor Red
}

Write-Host ""
