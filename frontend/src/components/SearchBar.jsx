import { forwardRef, useEffect } from 'react';
import { Search } from 'lucide-react';
import './SearchBar.css';

const SearchBar = forwardRef(function SearchBar(_props, ref) {
  useEffect(() => {
    function focusSearch(event) {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
        const input = ref?.current;
        if (input && window.getComputedStyle(input).visibility === 'visible' && input.getBoundingClientRect().width > 0) {
          event.preventDefault();
          input.focus();
        }
      }
    }
    window.addEventListener('keydown', focusSearch);
    return () => window.removeEventListener('keydown', focusSearch);
  }, [ref]);

  return <label className="search-bar clay-input">
    <Search className="search-bar__icon" size={17} aria-hidden="true" />
    <input ref={ref} type="search" aria-label="Search Intellivest" placeholder="Search Intellivest..." />
    <kbd className="search-bar__shortcut clay-chip" aria-hidden="true">⌘K</kbd>
  </label>;
});

export default SearchBar;
