/** Build: npx tailwindcss@3.4.17 -c tailwind.config.js -i tailwind-input.css -o tailwind.css --minify */
module.exports = {
    content: ['./*.html', './blog/**/*.html', './case-studies/**/*.html'],
    theme: {
        extend: {
            colors: {
                navy: { 50:'#f0f3fa',100:'#dce2f0',200:'#b8c4e1',300:'#94a6d2',400:'#7088c3',500:'#4E6AAF',600:'#3e5590',700:'#2e4070',800:'#1e2b50',900:'#111a33' },
                fire: { 50:'#fef2ee',100:'#fde0d6',200:'#fbbcab',300:'#f89075',400:'#f4633f',500:'#E84425',600:'#c2341b',700:'#922716',800:'#631b10',900:'#3d110a' }
            },
            fontFamily: { sans: ['Inter','system-ui','-apple-system','sans-serif'] }
        }
    }
}
