// Only these standalone print-layout commands have no meaning in the web edition.
const command = /\\(?:[Nn]eedspace\{\d+(?:\.\d+)?\\baselineskip\}|(?:newpage|clearpage|par|smallskip|medskip|bigskip)\b)/g;
export function isPrintLayout(text) {
  return text.trim() !== '' && text.replace(command, '').trim() === '';
}
export function stripPrintLines(text) {
  return text.replace(/^\\[^\n]*$/gm, line => isPrintLayout(line) ? '' : line);
}
