let booksByAuthor = {};
let alphabetSet = new Set();
let flatGridOriginalOrder = [];
let isColorSorted = false;
let currentCoverSize = 175; // Track current cover size


fetch('books.json')
    .then(res => res.json())
    .then(books => {
        books.forEach(book => {
            const author = book.author || "Unknown Author";
            const series = book.series || "No Series";

            if (!booksByAuthor[author]) booksByAuthor[author] = {};
            if (!booksByAuthor[author][series]) booksByAuthor[author][series] = [];

            booksByAuthor[author][series].push(book);
            alphabetSet.add(author[0].toUpperCase());
        });

        renderAlphabetNav([...alphabetSet].sort());
        renderLibrary(booksByAuthor);
        setupSlider();
        setupMobileSizeControls();

        document.getElementById('search').addEventListener('input', e => {
            filterBooks(e.target.value.trim().toLowerCase());
        });
    });

function renderAlphabetNav(letters) {
    const nav = document.getElementById('alphabet-jump');
    letters.forEach(letter => {
        const btn = document.createElement('button');
        btn.textContent = letter;
        btn.onclick = () => {
            const section = document.querySelector(`[data-letter='${letter}']`);
            if (section) section.scrollIntoView({behavior: 'smooth'});
        };
        nav.appendChild(btn);
    });
}

function createBookImage(book) {
    const img = document.createElement('img');
    img.className = 'book-cover';
    img.src = book.cover_path;
    img.alt = book.title;

    img.dataset.author = book.author || '';
    img.dataset.series = book.series || '';

    img.addEventListener('mousemove', e => showTooltip(e, book));
    img.addEventListener('mouseleave', hideTooltip);

    if (book.cover_color) {
        const [r, g, b] = book.cover_color;
        const [h] = rgbToHsl(r, g, b); // hue only
        img.dataset.hue = h;
    }

    return img;
}

function rgbToHsl(r, g, b) {
    r /= 255;
    g /= 255;
    b /= 255;
    const max = Math.max(r, g, b), min = Math.min(r, g, b);
    let h, s, l = (max + min) / 2;
    if (max === min) {
        h = s = 0; // achromatic
    } else {
        const d = max - min;
        s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
        switch (max) {
            case r:
                h = ((g - b) / d + (g < b ? 6 : 0));
                break;
            case g:
                h = ((b - r) / d + 2);
                break;
            case b:
                h = ((r - g) / d + 4);
                break;
        }
        h /= 6;
    }
    return [Math.round(h * 360), s, l]; // return hue, saturation, lightness
}

function renderLibrary(data) {
    const container = document.getElementById('library');
    container.innerHTML = '';

    let flatGrid = document.createElement('div');
    flatGrid.className = 'book-grid-flat';
    flatGrid.style.display = 'none';
    flatGrid.id = 'flat-grid';

    flatGridOriginalOrder = [];  // reset original order list

    Object.keys(data).sort().forEach(author => {
        const authorSection = document.createElement('section');
        authorSection.className = 'author-section';
        authorSection.id = `author-${author}`;
        authorSection.setAttribute('data-letter', author[0].toUpperCase());

        const authorTitle = document.createElement('h2');
        authorTitle.textContent = author;
        authorSection.appendChild(authorTitle);

        const seriesMap = data[author];
        const seriesList = Object.keys(seriesMap).sort();
        const hideNoSeriesTitle = seriesList.length === 1 && seriesList[0] === 'No Series';

        seriesList.forEach(series => {
            const seriesSection = document.createElement('div');
            seriesSection.className = 'series-section';

            if (!hideNoSeriesTitle || series !== 'No Series') {
                const seriesTitle = document.createElement('h3');
                seriesTitle.textContent = series;
                seriesSection.appendChild(seriesTitle);
            }

            const grid = document.createElement('div');
            grid.className = 'book-grid';

            seriesMap[series]
                .sort((a, b) => (a.series_index || 0) - (b.series_index || 0) || a.title.localeCompare(b.title))
                .forEach(book => {
                    const image = createBookImage(book);
                    grid.appendChild(image);
                    const clone = image.cloneNode(true);
                    flatGrid.appendChild(clone);
                    flatGridOriginalOrder.push(clone);
                });

            seriesSection.appendChild(grid);
            authorSection.appendChild(seriesSection);
        });

        container.appendChild(authorSection);
    });

    container.appendChild(flatGrid);
}

function showTooltip(e, book) {
    const tooltip = document.getElementById('tooltip');
    tooltip.innerHTML = `
    <strong>${book.title}</strong><br>
    <em>${book.author}</em><br>
    ${book.series ? `${book.series} #${book.series_index}<br>` : ''}
  `;

    const margin = 20;
    const tooltipWidth = 300;
    const tooltipHeight = 120;

    let left = e.pageX + 15;
    let top = e.pageY + 15;

    const maxLeft = window.innerWidth - tooltipWidth - margin;
    const maxTop = window.innerHeight - tooltipHeight - margin;

    tooltip.style.left = `${Math.min(left, maxLeft)}px`;
    tooltip.style.top = `${Math.min(top, maxTop)}px`;
    tooltip.classList.remove('hidden');
}

function hideTooltip() {
    document.getElementById('tooltip').classList.add('hidden');
}

function setupSlider() {
    const slider = document.getElementById('size-slider');
    currentCoverSize = parseInt(slider.value);
    document.documentElement.style.setProperty('--cover-size', `${currentCoverSize}px`);
    slider.addEventListener('input', () => {
        currentCoverSize = parseInt(slider.value);
        document.documentElement.style.setProperty('--cover-size', `${currentCoverSize}px`);
    });
}

function setupMobileSizeControls() {
    const plusBtn = document.getElementById('size-plus');
    const minusBtn = document.getElementById('size-minus');

    if (plusBtn && minusBtn) {
        plusBtn.addEventListener('click', () => {
            currentCoverSize = Math.min(currentCoverSize + 20, 400);
            document.documentElement.style.setProperty('--cover-size', `${currentCoverSize}px`);
        });

        minusBtn.addEventListener('click', () => {
            currentCoverSize = Math.max(currentCoverSize - 20, 100);
            document.documentElement.style.setProperty('--cover-size', `${currentCoverSize}px`);
        });
    }
}

document.getElementById('toggle-view').addEventListener('click', () => {
    document.body.classList.toggle('flat-view');
    const isFlat = document.body.classList.contains('flat-view');

    document.getElementById('flat-grid').style.display = isFlat ? 'flex' : 'none';
    document.getElementById('toggle-view').textContent = isFlat ? 'Structured View' : 'Flat View';
    document.getElementById('sort-color').classList.toggle('hidden', !isFlat);

    // Reset sort toggle
    isColorSorted = false;
    document.getElementById('sort-color').textContent = "Sort by Color";
});

document.getElementById('sort-color').addEventListener('click', () => {
    const grid = document.getElementById('flat-grid');
    const button = document.getElementById('sort-color');

    if (!isColorSorted) {
        // Sort by hue
        const sorted = Array.from(grid.querySelectorAll('.book-cover')).sort((a, b) => {
            const ah = parseFloat(a.dataset.hue) || 0;
            const bh = parseFloat(b.dataset.hue) || 0;
            return ah - bh;
        });

        sorted.forEach(img => grid.appendChild(img));
        isColorSorted = true;
        button.textContent = "Original Order";
    } else {
        flatGridOriginalOrder.forEach(img => grid.appendChild(img));
        isColorSorted = false;
        button.textContent = "Sort by Color";
    }
});

function filterBooks(query) {
    const isFlat = document.body.classList.contains('flat-view');

    if (!query) {
        document.querySelectorAll('.book-cover').forEach(img => img.style.display = '');
        document.querySelectorAll('.author-section, .series-section').forEach(section => section.style.display = '');
        return;
    }

    if (isFlat) {
        document.querySelectorAll('#flat-grid .book-cover').forEach(img => {
            const text = `${img.alt} ${img.dataset.author} ${img.dataset.series}`.toLowerCase();
            img.style.display = text.includes(query) ? '' : 'none';
        });
    } else {
        document.querySelectorAll('.author-section').forEach(authorSec => {
            let showAuthor = false;

            authorSec.querySelectorAll('.series-section').forEach(seriesSec => {
                let showSeries = false;

                seriesSec.querySelectorAll('.book-cover').forEach(img => {
                    const text = `${img.alt} ${img.dataset.author} ${img.dataset.series}`.toLowerCase();
                    const match = text.includes(query);
                    img.style.display = match ? '' : 'none';
                    if (match) showSeries = true;
                });

                seriesSec.style.display = showSeries ? '' : 'none';
                if (showSeries) showAuthor = true;
            });

            authorSec.style.display = showAuthor ? '' : 'none';
        });
    }
}