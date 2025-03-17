// sort.js
window.onload = function() {
    document.getElementById('sort-seed').addEventListener('click', function() {
        sortList('seed');
    });

    document.getElementById('sort-true-seed').addEventListener('click', function() {
        sortList('true-seed');
    });
}

function sortList(sortType) {
    var list, i, switching, b, shouldSwitch;
    list = document.getElementById("seed-list");
    switching = true;
    while (switching) {
        switching = false;
        b = list.getElementsByTagName("LI");
        for (i = 0; i < (b.length - 1); i++) {
            shouldSwitch = false;
            if (sortType == 'seed' && parseInt(b[i].getAttribute('data-seed')) > parseInt(b[i + 1].getAttribute('data-seed'))) {
                shouldSwitch = true;
                break;
            }
            if (sortType == 'true-seed' && parseInt(b[i].getAttribute('data-true-seed')) > parseInt(b[i + 1].getAttribute('data-true-seed'))) {
                shouldSwitch = true;
                break;
            }
        }
        if (shouldSwitch) {
            b[i].parentNode.insertBefore(b[i + 1], b[i]);
            switching = true;
        }
    }
}