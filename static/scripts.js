document.addEventListener("DOMContentLoaded", function () { 
    fetchStockLevels();
});

function fetchStockLevels() {
    fetch("/api/stock-levels")
        .then(response => response.json())
        .then(data => {
            let stockTable = document.getElementById("stock-table-body");
            stockTable.innerHTML = "";
            data.forEach(item => {
                let row = `<tr>
                    <td>${item.id}</td>
                    <td>${item.type}</td>
                    <td>${item.stock}</td>
                </tr>`;
                stockTable.innerHTML += row;
            });
        })
        .catch(error => console.error("Error fetching stock levels:", error));
}
