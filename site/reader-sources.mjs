const entries = new Set(['README.md', 'README.en.md', 'LICENSE.md', 'references.md', 'course/README.md', 'projects/README.md', 'projects/PROJECT_READER.md', 'workbook/README.md', 'loom/README.md', 'docs/README.md', 'docs/legal/ACKNOWLEDGEMENTS.md', 'docs/legal/THIRD_PARTY_NOTICES.md', 'docs/legal/RIGHTS_REVIEW.md', 'docs/maintenance/REPOSITORY_STATUS.md', '.github/CONTRIBUTING.md', '.github/SUPPORT.md']);

export function isReaderSource(file) {
  if (!file.endsWith('.md') || /(?:^|\/)(?:qa|provenance|build)(?:\/|$)/.test(file)) return false;
  return entries.has(file)
    || /^course\/(?:zh|en)\/chapters\/ch\d{2}\/(?:content|source_notes)\.md$/.test(file)
    || /^editions\/(?:zh|en)\/(?:README\.md|NOTEBOOK_GUIDE\.md|OPTIONAL_DATA\.md|MARKET_EMPIRICAL_STATUS\.md|LOCAL_VALIDATION\.md|REMAINING_ITEMS\.md|FILE_TREE\.md|resources\/[^/]+\.md|(?:projects|capstone)\/)/.test(file)
    || /^(?:projects\/project\d{2}|capstone)\//.test(file);
}
