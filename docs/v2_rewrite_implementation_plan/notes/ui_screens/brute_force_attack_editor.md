```html
<!--  Modal: New Brute Force Attack -->
<form class="p-6 dark:bg-gray-800 bg-white rounded-lg shadow" hx-post="/api/v1/web/attacks/" hx-swap="outerHTML" hx-target="#attack-list">
 <!-- Header -->
 <h3 class="text-xl font-bold dark:text-white mb-4">
  New Brute Force Attack
 </h3>
 <!--  Mask Length -->
 <div class="grid grid-cols-2 gap-4 mb-4">
  <div>
   <label class="block mb-2 text-sm font-medium text-gray-900 dark:text-white" for="increment_minimum">
    Min Length
   </label>
   <input class="form-input w-full" id="increment_minimum" min="1" name="increment_minimum" required="" type="number"/>
  </div>
  <div>
   <label class="block mb-2 text-sm font-medium text-gray-900 dark:text-white" for="increment_maximum">
    Max Length
   </label>
   <input class="form-input w-full" id="increment_maximum" max="64" name="increment_maximum" required="" type="number"/>
  </div>
 </div>
 <!-- 🔠 Charset Selection -->
 <div class="mb-4">
  <label class="block mb-2 text-sm font-medium text-gray-900 dark:text-white">
   Character Sets
  </label>
  <div class="grid grid-cols-2 gap-2">
   <label class="flex items-center">
    <input checked="" class="form-checkbox" name="charset_lowercase" type="checkbox"/>
    <span class="ml-2 text-sm text-gray-900 dark:text-white">
     Lowercase (a-z)
    </span>
   </label>
   <label class="flex items-center">
    <input checked="" class="form-checkbox" name="charset_uppercase" type="checkbox"/>
    <span class="ml-2 text-sm text-gray-900 dark:text-white">
     Uppercase (A-Z)
    </span>
   </label>
   <label class="flex items-center">
    <input checked="" class="form-checkbox" name="charset_digits" type="checkbox"/>
    <span class="ml-2 text-sm text-gray-900 dark:text-white">
     Digits (0-9)
    </span>
   </label>
   <label class="flex items-center">
    <input checked="" class="form-checkbox" name="charset_special" type="checkbox"/>
    <span class="ml-2 text-sm text-gray-900 dark:text-white">
     Symbols (!@#$)
    </span>
   </label>
  </div>
 </div>
 <!--  Custom Charset Preview -->
 <div class="mb-4">
  <label class="block mb-2 text-sm font-medium text-gray-900 dark:text-white">
   Charset Preview (?1)
  </label>
  <input class="form-input w-full bg-gray-100 dark:bg-gray-700" readonly="" type="text" value="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$"/>
 </div>
 <!--  Generated Mask Preview -->
 <div class="mb-4">
  <label class="block mb-2 text-sm font-medium text-gray-900 dark:text-white">
   Generated Mask
  </label>
  <input class="form-input w-full bg-gray-100 dark:bg-gray-700" id="generated_mask" readonly="" type="text" value="?1?1?1?1?1?1"/>
 </div>
 <!-- 🧮 Keyspace + Complexity Meter -->
 <div class="mb-4 text-sm text-gray-900 dark:text-white">
  <p>
   <strong>
    Estimated Keyspace:
   </strong>
   56800235584
  </p>
  <p>
   <strong>
    Complexity:
   </strong>
   <span class="inline-flex items-center space-x-1">
    <span class="w-2 h-2 bg-green-400 rounded-full">
    </span>
    <span class="w-2 h-2 bg-green-400 rounded-full">
    </span>
    <span class="w-2 h-2 bg-green-400 rounded-full">
    </span>
    <span class="w-2 h-2 bg-gray-600 rounded-full">
    </span>
    <span class="w-2 h-2 bg-gray-600 rounded-full">
    </span>
   </span>
  </p>
 </div>
 <!-- 🔘 Buttons -->
 <div class="flex justify-end space-x-2">
  <button class="btn btn-primary" type="submit">
   Save
  </button>
  <button class="btn btn-secondary" data-modal-hide="bruteforceModal" type="button">
   Cancel
  </button>
 </div>
</form>
```

---

### Implementation Notes for Skirmish

- Modal component: use Flowbite’s `Modal`

- Use `hx-post` to `/api/v1/web/attacks/`

- Live-update `?1` charset string and mask string via HTMX triggers on checkbox and input fields

- Call backend `POST /api/v1/web/attacks/estimate` for live keyspace/complexity

- Persist to backend with:

  ```python
  attack.attack_mode = "mask"
  attack.attack_mode_hashcat = 3
  attack.increment_mode = True
  attack.increment_minimum = min_len
  attack.increment_maximum = max_len
  attack.mask = "?1" * max_len
  attack.custom_charset_1 = charset_str
  ```

- Add validation for malformed input

- Respect `disable_markov`, `optimized`, and workload profile defaults
