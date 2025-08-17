let booksByAuthor = {};
let alphabetSet = new Set();
let flatGridOriginalOrder = [];
let isColorSorted = false;
let currentCoverSize = 175;
let currentViewMode = 'structured';


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
        renderTextLibrary(booksByAuthor);
        setupSlider();
        setupMobileSizeControls();
        setupViewModeSelector();

        document.getElementById('search').addEventListener('input', e => {
            filterBooks(e.target.value.trim().toLowerCase());
        });
    });

function setupViewModeSelector() {
    const viewSelect = document.getElementById('view-mode');
    const sortColorBtn = document.getElementById('sort-color');

    viewSelect.addEventListener('change', () => {
        const selectedMode = viewSelect.value;
        currentViewMode = selectedMode;

        // Remove all view classes
        document.body.classList.remove('flat-view', 'text-view');

        // Hide all view containers
        document.getElementById('flat-grid').style.display = 'none';
        document.getElementById('text-list').style.display = 'none';
        sortColorBtn.classList.add('hidden');

        // Reset sort state
        isColorSorted = false;
        sortColorBtn.textContent = "Sort by Color";

        switch(selectedMode) {
            case 'flat':
                document.body.classList.add('flat-view');
                document.getElementById('flat-grid').style.display = 'flex';
                sortColorBtn.classList.remove('hidden');
                break;
            case 'text':
                document.body.classList.add('text-view');
                document.getElementById('text-list').style.display = 'block';
                break;
            case 'structured':
            default:
                // Structured view is the default state
                break;
        }
    });
}

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

    // Wrap image to allow positioned overlay badge
    const wrapper = document.createElement('div');
    wrapper.className = 'cover-wrapper';
    wrapper.appendChild(img);

    // Add green check badge if marked as read
    if (book.is_read) {
        const badge = document.createElement('span');
        badge.className = 'read-badge';
        badge.title = 'Read';
        badge.textContent = '✓';
        wrapper.appendChild(badge);
    }

    return wrapper;
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

function renderTextLibrary(data) {
    const container = document.getElementById('library');

    let textList = document.createElement('div');
    textList.className = 'text-list';
    textList.id = 'text-list';

    Object.keys(data).sort().forEach(author => {
        const authorSection = document.createElement('section');
        authorSection.className = 'text-author-section';
        authorSection.id = `text-author-${author}`;
        authorSection.setAttribute('data-letter', author[0].toUpperCase());

        const authorTitle = document.createElement('h2');
        authorTitle.textContent = author;
        authorSection.appendChild(authorTitle);

        const seriesMap = data[author];
        const seriesList = Object.keys(seriesMap).sort();
        const hideNoSeriesTitle = seriesList.length === 1 && seriesList[0] === 'No Series';

        seriesList.forEach(series => {
            const seriesSection = document.createElement('div');
            seriesSection.className = 'text-series-section';

            if (!hideNoSeriesTitle || series !== 'No Series') {
                const seriesTitle = document.createElement('h3');
                seriesTitle.textContent = series;
                seriesSection.appendChild(seriesTitle);
            }

            const bookList = document.createElement('div');
            bookList.className = 'text-book-list';

            seriesMap[series]
                .sort((a, b) => (a.series_index || 0) - (b.series_index || 0) || a.title.localeCompare(b.title))
                .forEach(book => {
                    const bookItem = document.createElement('div');
                    bookItem.className = 'text-book-item';
                    bookItem.dataset.author = book.author || '';
                    bookItem.dataset.series = book.series || '';
                    bookItem.dataset.title = book.title || '';

                    const title = document.createElement('div');
                    title.className = 'text-book-title';
                    title.textContent = book.title || 'Untitled';

                    bookItem.appendChild(title);
                    bookList.appendChild(bookItem);
                });

            seriesSection.appendChild(bookList);
            authorSection.appendChild(seriesSection);
        });

        textList.appendChild(authorSection);
    });

    container.appendChild(textList);
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
        // Sort wrappers by the inner image's hue
        const wrappers = Array.from(grid.querySelectorAll('.cover-wrapper'));
        wrappers.sort((wa, wb) => {
            const a = wa.querySelector('.book-cover');
            const b = wb.querySelector('.book-cover');
            const ah = parseFloat(a?.dataset.hue) || 0;
            const bh = parseFloat(b?.dataset.hue) || 0;
            return ah - bh;
        });
        wrappers.forEach(w => grid.appendChild(w));
        isColorSorted = true;
        button.textContent = "Original Order";
    } else {
        flatGridOriginalOrder.forEach(w => grid.appendChild(w));
        isColorSorted = false;
        button.textContent = "Sort by Color";
    }
});

function filterBooks(query) {
    if (!query) {
        // Show all items in all views
        document.querySelectorAll('.cover-wrapper').forEach(w => w.style.display = '');
        document.querySelectorAll('.author-section, .series-section').forEach(section => section.style.display = '');
        document.querySelectorAll('.text-book-item').forEach(item => item.style.display = '');
        document.querySelectorAll('.text-author-section, .text-series-section').forEach(section => section.style.display = '');
        return;
    }

    if (currentViewMode === 'flat') {
        document.querySelectorAll('#flat-grid .cover-wrapper').forEach(w => {
            const img = w.querySelector('.book-cover');
            const text = `${img?.alt || ''} ${img?.dataset.author || ''} ${img?.dataset.series || ''}`.toLowerCase();
            w.style.display = text.includes(query) ? '' : 'none';
        });
    } else if (currentViewMode === 'text') {
        // ... existing code ...
    } else {
        // Structured view
        document.querySelectorAll('.author-section').forEach(authorSec => {
            let showAuthor = false;

            authorSec.querySelectorAll('.series-section').forEach(seriesSec => {
                let showSeries = false;

                seriesSec.querySelectorAll('.cover-wrapper').forEach(w => {
                    const img = w.querySelector('.book-cover');
                    const text = `${img?.alt || ''} ${img?.dataset.author || ''} ${img?.dataset.series || ''}`.toLowerCase();
                    const match = text.includes(query);
                    w.style.display = match ? '' : 'none';
                    if (match) showSeries = true;
                });

                seriesSec.style.display = showSeries ? '' : 'none';
                if (showSeries) showAuthor = true;
            });

            authorSec.style.display = showAuthor ? '' : 'none';
        });
    }
}