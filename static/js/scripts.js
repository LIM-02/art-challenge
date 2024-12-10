// Global user role (can be 'manager' or 'viewer')
const userRole = 'manager'; // Change dynamically if needed

// DOM Elements
const inventorySection = document.getElementById('inventory-section');
const inboundSection = document.getElementById('inbound-section');
const outboundSection = document.getElementById('outbound-section');
const addProductSection = document.getElementById('add-product-section');

// Event Listeners for Navigation Buttons
document.getElementById('inventory-button').addEventListener('click', () => {
    inventorySection.style.display = 'block';
    inboundSection.style.display = 'none';
    outboundSection.style.display = 'none';
    loadProducts();
});

document.getElementById('inbound-button').addEventListener('click', () => {
    inventorySection.style.display = 'none';
    outboundSection.style.display = 'none';
    inboundSection.style.display = 'block';

    // Show inbound pagination controls
    document.getElementById('pagination-controls-inbound').classList.remove('hidden');

    // Load Inbound Records
    loadInbound();
});

document.getElementById('outbound-button').addEventListener('click', () => {
    inventorySection.style.display = 'none';
    inboundSection.style.display = 'none';
    outboundSection.style.display = 'block';

    document.getElementById('pagination-controls-outbound').classList.remove('hidden');

    loadOutbound();
});


// Fetch and Display Products with Pagination
function loadProducts(offset = 0) {
    fetch(`/products?limit=${limit}&offset=${offset}`)
        .then(response => response.json())
        .then(data => {
            const productTableBody = document.querySelector("#productTable tbody");
            productTableBody.innerHTML = ""; // Clear existing rows

            if (data.length === 0 && currentOffset > 0) {
                alert('No more records to display');
                currentOffset -= limit; // Prevent invalid offset
                return;
            }

            data.forEach(product => {
                let actions = `
                    <button class="px-3 py-1 bg-blue-500 text-white rounded-md hover:bg-blue-600" onclick="viewProduct(${product.product_id})">View</button>
                `;
                if (userRole === 'manager') {
                    actions += `
                        <button class="px-3 py-1 bg-green-500 text-white rounded-md hover:bg-green-600" onclick="editProduct(${product.product_id})">Edit</button>
                        <button class="px-3 py-1 bg-red-500 text-white rounded-md hover:bg-red-600" onclick="deleteProduct(${product.product_id})">Delete</button>
                    `;
                }
                const row = `
                    <tr>
                        <td>${product.product_id}</td>
                        <td>${product.product_name}</td>
                        <td>${product.tags}</td>
                        <td>${product.description}</td>
                        <td>${product.quantity}</td>
                        <td>${actions}</td>
                    </tr>
                `;
                productTableBody.innerHTML += row;
            });

            // Enable/Disable Pagination Buttons
            document.getElementById('prev-button').disabled = offset === 0;
            document.getElementById('next-button').disabled = data.length < limit;
        })
        .catch(error => console.error("Error fetching products:", error));
}


// Global variables for pagination
let inventoryOffset = 0;
let inboundOffset = 0;
let outboundOffset = 0;
const limit = 10;

// Inventory Pagination
document.getElementById('prev-button').addEventListener('click', () => {
    if (inventoryOffset > 0) {
        inventoryOffset -= limit;
        loadProducts(inventoryOffset);
    }
});

document.getElementById('next-button').addEventListener('click', () => {
    inventoryOffset += limit;
    loadProducts(inventoryOffset);
});

// Inbound Pagination
document.getElementById('prev-inbound-button').addEventListener('click', () => {
    if (inboundOffset > 0) {
        inboundOffset -= limit;
        loadInbound(inboundOffset);
    }
});

document.getElementById('next-inbound-button').addEventListener('click', () => {
    inboundOffset += limit;
    loadInbound(inboundOffset);
});

// Outbound Pagination
document.getElementById('prev-outbound-button').addEventListener('click', () => {
    if (outboundOffset > 0) {
        outboundOffset -= limit;
        loadOutbound(outboundOffset);
    }
});

document.getElementById('next-outbound-button').addEventListener('click', () => {
    outboundOffset += limit;
    loadOutbound(outboundOffset);
});

// Enable/Disable Pagination Buttons Dynamically
function updatePaginationControls(type, offset, dataLength) {
    if (type === "inbound") {
        const prevButton = document.getElementById("prev-inbound-button");
        const nextButton = document.getElementById("next-inbound-button");

        // Disable Previous button if at the first page
        if (offset === 0) {
            prevButton.disabled = true;
        } else {
            prevButton.disabled = false;
        }

        // Disable Next button if fewer records than the limit are returned
        if (dataLength < limit) {
            nextButton.disabled = true;
        } else {
            nextButton.disabled = false;
        }
    }

    // Similar logic for outbound (if needed)
    if (type === "outbound") {
        const prevButton = document.getElementById("prev-outbound-button");
        const nextButton = document.getElementById("next-outbound-button");

        if (offset === 0) {
            prevButton.disabled = true;
        } else {
            prevButton.disabled = false;
        }

        if (dataLength < limit) {
            nextButton.disabled = true;
        } else {
            nextButton.disabled = false;
        }
    }
}


// Add Product
if (userRole === 'manager') {
    document.getElementById('addProductForm').addEventListener('submit', function (e) {
        e.preventDefault();
        const formData = new FormData(this);
        const data = Object.fromEntries(formData);
        fetch('/products', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        })
            .then(response => response.json())
            .then(result => {
                alert(result.message);
                loadProducts();
                this.reset();
            });
    });
}

// View Product Details
function viewProduct(product_id) {
    fetch(`/products/${product_id}`)
        .then(response => response.json())
        .then(product => {
            alert(`Product Details:\n\nID: ${product.product_id}\nName: ${product.product_name}\nTags: ${product.tags}\nDescription: ${product.description}\nQuantity: ${product.quantity}`);
        });
}

// Delete Product
function deleteProduct(product_id) {
    fetch(`/products/${product_id}`, {
        method: 'DELETE'
    })
        .then(response => response.json())
        .then(result => {
            alert(result.message);
            loadProducts();
        });
}

function editProduct(product_id) {
    // Fetch product details from API
    fetch(`/products/${product_id}`)
        .then(response => response.json())
        .then(product => {
            // Populate form fields
            document.getElementById('edit-product-id').value = product.product_id;
            document.getElementById('edit-product-name').value = product.product_name;
            document.getElementById('edit-product-tags').value = product.tags;
            document.getElementById('edit-product-quantity').value = product.quantity;
            document.getElementById('edit-product-description').value = product.description;

            // Show the modal
            document.getElementById('edit-modal').style.display = 'flex';
        })
        .catch(error => console.error('Error fetching product details:', error));
}

function closeEditModal() {
    // Hide the modal
    document.getElementById('edit-modal').style.display = 'none';
}

// Submit form
document.getElementById('edit-form').addEventListener('submit', function (e) {
    e.preventDefault();

    const updatedProduct = {
        product_id: document.getElementById('edit-product-id').value,
        product_name: document.getElementById('edit-product-name').value,
        tags: document.getElementById('edit-product-tags').value,
        quantity: document.getElementById('edit-product-quantity').value,
        description: document.getElementById('edit-product-description').value,
    };

    fetch(`/products/${updatedProduct.product_id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updatedProduct),
    })
        .then(response => response.json())
        .then(result => {
            alert(result.message || 'Product updated successfully!');
            loadProducts(); // Reload the product list
            closeEditModal(); // Hide the modal
        })
        .catch(error => console.error('Error updating product:', error));
});




// Initial Load
loadProducts();
if (userRole === 'manager') {
    addProductSection.style.display = 'block';
}

// Fetch and Display Inbound Records
function loadInbound(offset = 0) {
    fetch(`/inbound?limit=${limit}&offset=${offset}`)
        .then(response => response.json())
        .then(data => {
            const inboundTableBody = document.querySelector("#inboundTable tbody");
            inboundTableBody.innerHTML = ""; // Clear existing rows

            if (data.length === 0 && offset === 0) {
                inboundTableBody.innerHTML = `<tr><td colspan="8">No inbound records found</td></tr>`;
                return;
            }

            data.forEach(record => {
                const row = `
                    <tr>
                        <td>${record.reference}</td>
                        <td>${record.product_sku}</td>
                        <td>${record.product_id}</td>
                        <td>${record.supplier_id}</td>
                        <td>${record.quantity_received}</td>
                        <td>${record.received_date}</td>
                        <td>${record.location}</td>
                        <td>${record.remarks}</td>
                    </tr>
                `;
                inboundTableBody.innerHTML += row;
            });

            updatePaginationControls("inbound", offset, data.length);
        })
        .catch(error => console.error("Error fetching inbound records:", error));
}

document.getElementById('inboundForm').addEventListener('submit', function (e) {
    e.preventDefault();
    const formData = new FormData(this);
    const data = Object.fromEntries(formData);

    fetch('/inbound', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
        .then(response => response.json())
        .then(result => {
            if (result.message) {
                alert(result.message);
                loadInbound();
                loadProducts();
            } else {
                alert(result.error || 'Error logging inbound record');
            }
            this.reset();
        })
        .catch(error => alert('Error: ' + error.message));
});


// Fetch and Display Outbound Records
function loadOutbound(offset = 0) {
    fetch(`/outbound?limit=${limit}&offset=${offset}`)
        .then(response => response.json())
        .then(data => {
            const outboundTableBody = document.querySelector("#outboundTable tbody");
            outboundTableBody.innerHTML = ""; // Clear existing rows

            if (data.length === 0 && offset === 0) {
                outboundTableBody.innerHTML = `<tr><td colspan="5">No outbound records found</td></tr>`;
                return;
            }

            data.forEach(record => {
                const row = `
                    <tr>
                        <td>${record.outbound_id}</td>
                        <td>${record.product_id}</td>
                        <td>${record.customer_id}</td>
                        <td>${record.quantity_sent}</td>
                        <td>${record.sent_date}</td>
                    </tr>
                `;
                outboundTableBody.innerHTML += row;
            });

            // Update Pagination Buttons
            updatePaginationControls("outbound", offset, data.length);
        })
        .catch(error => console.error("Error fetching outbound records:", error));
}



// Submit New Outbound Record
document.getElementById('outbound-form').addEventListener('submit', function (e) {
    e.preventDefault();
    const formData = new FormData(this);
    const data = Object.fromEntries(formData);
    console.log('Outbound Payload:', data); // Debugging payload

    fetch('/outbound', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
        .then(response => response.json())
        .then(result => {
            if (result.message) {
                alert(result.message);
                loadOutbound();
                loadProducts(); // Update inventory
            } else {
                alert(result.error || 'Error logging outbound record');
            }
            this.reset(); // Reset the form
        })
        .catch(error => alert('Error: ' + error.message));
});



