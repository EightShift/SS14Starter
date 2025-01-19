function crel(type, attrs) {
    let element = document.createElement(type);

    if (attrs) {
        for (var [key, value] of Object.entries(attrs)) {
            if (key == "text") {
                element.innerText = value;

            } else if (key == "html") {
                element.innerHTML = value;

            } else {
                element.setAttribute(key, value);

            }
        }
    }

    return element
}


function findArrInList(list, key, value) {
    for (var i = 0; i < list.length; i++) {
        if (list[i][key] == value) {
            return list[i];
        }
    }
}


function set_tooltip(element, title, options) {
    UIkit.tooltip(element).show();
    element.setAttribute('uk-tooltip', `title: ${fields.start_local_server.toUpperCase()}; offset: ${tooltip_offset}; pos: top-left;`);
}

Element.prototype.removeAllChildren = Element.prototype.removeAllChildren || function () {
    while (this.firstChild) {
        this.removeChild(this.lastChild);
    }
};



// QUANTIZER

function arrays_equal(a1, a2) {
    if (a1.length !== a2.length) return false;
    for (var i = 0; i < a1.length; ++i) {
        if (a1[i] !== a2[i]) return false;
    }
    return true;
};


function get_pixel_dataset(context) {
    var canvas_n_pixels = context.canvas.width * context.canvas.height;

    var flattened_dataset = context.getImageData(0, 0, context.canvas.width, context.canvas.height).data;
    var n_channels = flattened_dataset.length / canvas_n_pixels;
    var dataset = [];
    for (var i = 0; i < flattened_dataset.length; i += n_channels) {
        dataset.push(flattened_dataset.slice(i, i + n_channels));
    }

    return dataset;
};


function nearest_neighbor(point, neighbors) {
    var best_dist = Infinity;
    var best_index = -1;
    for (var i = 0; i < neighbors.length; ++i) {
        var neighbor = neighbors[i];
        var dist = 0;
        for (var j = 0; j < point.length; ++j) {
            dist += Math.pow(point[j] - neighbor[j], 2);
        }
        if (dist < best_dist) {
            best_dist = dist;
            best_index = i;
        }
    }
    return best_index;
};


function centroid(dataset) {
    if (dataset.length === 0) return [];

    var running_centroid = [];
    for (var i = 0; i < dataset[0].length; ++i) {
        running_centroid.push(0);
    }
    for (var i = 0; i < dataset.length; ++i) {
        var point = dataset[i];
        for (var j = 0; j < point.length; ++j) {
            running_centroid[j] += (point[j] - running_centroid[j]) / (i + 1);
        }
    }
    return running_centroid;
};


function k_means(dataset, k) {
    if (k === undefined) k = Math.min(3, dataset.length);

    rng_seed = 0;
    var random = function () {
        rng_seed = (rng_seed * 9301 + 49297) % 233280;
        return rng_seed / 233280;
    };

    centroids = [];
    for (var i = 0; i < k; ++i) {
        var idx = Math.floor(random() * dataset.length);
        centroids.push(dataset[idx]);
    }
    while (true) {
        var clusters = [];
        for (var i = 0; i < k; ++i) {
            clusters.push([]);
        }
        for (var i = 0; i < dataset.length; ++i) {
            var point = dataset[i];
            var nearest_centroid = nearest_neighbor(point, centroids);
            clusters[nearest_centroid].push(point);
        }
        let converged = true;
        for (var i = 0; i < k; ++i) {
            var cluster = clusters[i];
            var centroid_i = [];
            if (cluster.length > 0) {
                centroid_i = centroid(cluster);
            } else {
                var idx = Math.floor(random() * dataset.length);
                centroid_i = dataset[idx];
            }
            converged = arrays_equal(centroid_i, centroids[i]);
            centroids[i] = centroid_i;
        }

        if (converged) break;
    }
    return centroids;
};


function quantize(context, palette_size) {
    var pixel_dataset = get_pixel_dataset(context);
    var centroids = k_means(pixel_dataset, palette_size);

    var width = context.canvas.width;
    var height = context.canvas.height;

    var flattened_source_data = context.getImageData(0, 0, width, height).data;
    var n_pixels = width * height;
    var n_channels = flattened_source_data.length / n_pixels;

    var flattened_quantized_data = new Uint8ClampedArray(flattened_source_data.length);

    var current_pixel = new Uint8ClampedArray(n_channels);
    for (var i = 0; i < flattened_source_data.length; i += n_channels) {
        for (var j = 0; j < n_channels; ++j) {
            current_pixel[j] = flattened_source_data[i + j];
        }
        var nearest_color_index = nearest_neighbor(current_pixel, centroids);
        var nearest_color = centroids[nearest_color_index];
        for (var j = 0; j < nearest_color.length; ++j) {
            flattened_quantized_data[i + j] = nearest_color[j];
        }
    }

    var image = context.createImageData(width, height);
    image.data.set(flattened_quantized_data);

    context.putImageData(image, 0, 0);

};
