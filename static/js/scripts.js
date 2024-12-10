// Global user role (can be 'manager' or 'viewer')
const userRole = 'manager'; // Change dynamically if needed

// DOM Elements
const inventorySection = document.getElementById('inventory-section');
const inboundSection = document.getElementById('inbound-section');
const outboundSection = document.getElementById('outbound-section');
const addProductSection = document.getElementById('add-product-section');

// Global variables for pagination
let inventoryOffset = 0;
let inboundOffset = 0;
let outboundOffset = 0;
const limit = 10;

// Initialize the UI based on user role
function updateUIForRole() {
    if (userRole === 'manager') {
        if (addProductSection) addProductSection.style.display = 'block';
    } else {
        if (addProductSection) addProductSection.style.display = 'none';
    }
}
updateUIForRole();

// Event Listeners for Navigation Buttons
document.getElementById('inventory-button')?.addEventListener('click', () => {
    inventorySection.style.display = 'block';
    inboundSection.style.display = 'none';
    outboundSection.style.display = 'none';
    loadProducts();
});

document.getElementById('inbound-button')?.addEventListener('click', () => {
    inventorySection.style.display = 'none';
    outboundSection.style.display = 'none';
    inboundSection.style.display = 'block';
    loadInbound();
});

document.getElementById('outbound-button')?.addEventListener('click', () => {
    inventorySection.style.display = 'none';
    inboundSection.style.display = 'none';
    outboundSection.style.display = 'block';
    loadOutbound();
});

// Fetch and Display Products with Pagination
function loadProducts(offset = 0) {
    fetch(`/products?limit=${limit}&offset=${offset}`)
        .then(response => response.json())
        .then(data => {
            const productTableBody = document.querySelector("#productTable tbody");
            productTableBody.innerHTML = ""; // Clear existing rows

            if (data.length === 0 && offset > 0) {
                alert("No more records to display");
                return;
            }

            data.forEach(product => {
                const actions = `
                    <button class="px-3 py-1 bg-blue-500 text-white rounded-md hover:bg-blue-600" onclick="viewProduct('${product.sku}')">View</button>
                    ${userRole === 'manager' ? `
                    <button class="px-3 py-1 bg-green-500 text-white rounded-md hover:bg-green-600" onclick="editProduct('${product.sku}')">Edit</button>
                    <button class="px-3 py-1 bg-red-500 text-white rounded-md hover:bg-red-600" onclick="deleteProduct('${product.sku}')">Delete</button>
                    ` : ''}
                `;

                const row = `
                    <tr>
                        <td>${product.sku}</td>
                        <td>${product.product_name}</td>
                        <td>${product.category || "N/A"}</td>
                        <td>${product.description || "N/A"}</td>
                        <td>${product.quantity}</td>
                        <td>${product.location || "N/A"}</td>
                        <td>${product.supplier || "N/A"}</td>
                        <td>${actions}</td>
                    </tr>
                `;
                productTableBody.innerHTML += row;
            });

            document.getElementById("prev-button").disabled = offset === 0;
            document.getElementById("next-button").disabled = data.length < limit;
        })
        .catch(error => console.error("Error fetching products:", error));
}

// Add Product
if (userRole === 'manager') {
    document.addEventListener('DOMContentLoaded', () => {
        const addProductForm = document.getElementById('addProductForm');
        if (addProductForm) {
            addProductForm.addEventListener('submit', function (e) {
                e.preventDefault();
                const formData = new FormData(this);
                const data = Object.fromEntries(formData);

                fetch('/products', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data),
                })
                    .then(response => response.json())
                    .then(result => {
                        alert(result.message || 'Product added successfully');
                        loadProducts();
                        this.reset(); // Reset the form
                    })
                    .catch(error => console.error('Error adding product:', error));
            });
        }
    });
}

// View Product
function viewProduct(sku) {
    fetch(`/products/${sku}`)
        .then(response => response.json())
        .then(product => {
            alert(`Product Details:\nSKU: ${product.sku}\nName: ${product.product_name}\nCategory: ${product.category}\nDescription: ${product.description}\nQuantity: ${product.quantity}`);
        });
}

// Edit Product
function editProduct(sku) {
    fetch(`/products/${sku}`)
        .then(response => response.json())
        .then(product => {
            if (product.error) {
                alert(product.error);
                return;
            }
            // Populate modal form with product details
            document.getElementById('edit-product-id').value = product.sku;
            document.getElementById('edit-product-name').value = product.product_name;
            document.getElementById('edit-product-quantity').value = product.quantity;
            document.getElementById('edit-product-description').value = product.description;

            // Show the modal
            document.getElementById('edit-modal').style.display = 'flex';
        })
        .catch(error => console.error('Error fetching product details:', error));
}

// Function to close the modal
function closeEditModal() {
    document.getElementById('edit-modal').style.display = 'none';
}

// Function to handle form submission
document.getElementById('edit-form').addEventListener('submit', function (e) {
    e.preventDefault();

    const updatedProduct = {
        sku: document.getElementById('edit-product-id').value,
        product_name: document.getElementById('edit-product-name').value,
        quantity: document.getElementById('edit-product-quantity').value,
        description: document.getElementById('edit-product-description').value,
    };

    fetch(`/products/${updatedProduct.sku}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updatedProduct),
    })
        .then(response => response.json())
        .then(result => {
            alert(result.message || 'Product updated successfully!');
            closeEditModal(); // Hide the modal
            loadProducts(); // Reload the product list
        })
        .catch(error => console.error('Error updating product:', error));
});


// Delete Product
function deleteProduct(sku) {
    fetch(`/products/${sku}`, { method: 'DELETE' })
        .then(response => response.json())
        .then(result => {
            alert(result.message || 'Product deleted successfully');
            loadProducts();
        })
        .catch(error => console.error('Error deleting product:', error));
}

// Fetch and Display Inbound Records
function loadInbound(offset = 0) {
    fetch(`/inbound?limit=${limit}&offset=${offset}`)
        .then(response => response.json())
        .then(data => {
            const inboundTableBody = document.querySelector("#inboundTable tbody");
            inboundTableBody.innerHTML = "";

            if (data.length === 0) {
                inboundTableBody.innerHTML = `<tr><td colspan="8">No inbound records found</td></tr>`;
                return;
            }

            data.forEach(record => {
                const row = `
                    <tr>
                        <td>${record.reference}</td>
                        <td>${record.product_sku}</td>
                        <td>${record.supplier_id}</td>
                        <td>${record.quantity_received}</td>
                        <td>${record.received_date}</td>
                        <td>${record.location}</td>
                        <td>${record.remarks}</td>
                    </tr>
                `;
                inboundTableBody.innerHTML += row;
            });
        })
        .catch(error => console.error('Error fetching inbound records:', error));
}

// Fetch and Display Outbound Records
function loadOutbound(offset = 0) {
    fetch(`/outbound?limit=${limit}&offset=${offset}`)
        .then(response => response.json())
        .then(data => {
            const outboundTableBody = document.querySelector("#outboundTable tbody");
            outboundTableBody.innerHTML = "";

            if (data.length === 0) {
                outboundTableBody.innerHTML = `<tr><td colspan="8">No outbound records found</td></tr>`;
                return;
            }

            data.forEach(record => {
                const row = `
                    <tr>
                        <td>${record.reference}</td>
                        <td>${record.product_sku}</td>
                        <td>${record.customer_id}</td>
                        <td>${record.quantity_sent}</td>
                        <td>${record.sent_date}</td>
                        <td>${record.destination}</td>
                        <td>${record.remarks}</td>
                    </tr>
                `;
                outboundTableBody.innerHTML += row;
            });
        })
        .catch(error => console.error('Error fetching outbound records:', error));
}

// Initial Load
loadProducts();
