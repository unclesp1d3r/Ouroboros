## 📚 Page: New Dictionary Attack Dialog

This Flowbite modal allows users to configure a **Dictionary Attack**, selecting a wordlist, defining optional length constraints, and adding simple rule-like modifiers.

### 💡 Summary

- Form built using Flowbite modal structure
- HTMX-compatible submit to `/api/v1/web/attacks/`
- Dictionary is selected from a dropdown of available `AttackResourceFile` objects
- Modifiers correspond to rules applied on top of the dictionary input
- Displays estimated passwords to check and a dot-based complexity meter

---

### 🧱 Modal Header

```html
<h3 class="text-xl font-bold text-gray-900 dark:text-white">
 New Dictionary Attack
</h3>
<p class="text-sm text-gray-500 dark:text-gray-400">
 Dictionary Attack checks thousands of words from dictionary files as
    possible passwords.
</p>
```

---

### 🔢 Length Range

```html
<div class="grid grid-cols-2 gap-4 mb-4">
 <div>
  <label class="block text-sm font-medium text-gray-900 dark:text-white" for="min_length">
   Min Length
  </label>
  <input class="form-input w-full" id="min_length" name="min_length" type="number" value="1"/>
 </div>
 <div>
  <label class="block text-sm font-medium text-gray-900 dark:text-white" for="max_length">
   Max Length
  </label>
  <input class="form-input w-full" id="max_length" name="max_length" type="number" value="128"/>
 </div>
</div>
```

---

### 📂 Dictionary Selection (Dropdown)

The selected value here is `capitals-dictionary.txt`, containing 198 words. Use Flowbite `select` component populated via backend.

```html
<div class="mb-4">
 <label class="block text-sm font-medium text-gray-900 dark:text-white" for="dictionary_id">
  Dictionary
 </label>
 <select class="form-select w-full" id="dictionary_id" name="dictionary_id">
  <option value="xyz123">
   capitals-dictionary.txt (198 words)
  </option>
  <!-- Additional wordlists dynamically inserted -->
 </select>
</div>
```

This field maps to a selected `AttackResourceFile` with `resource_type = "word_list"`.

---

### 🎯 Pattern Field (Optional)

May be used to add a pattern-based constraint, shown with a help icon.

```html
<div class="mb-4">
 <label class="block text-sm font-medium text-gray-900 dark:text-white" for="pattern">
  Pattern
  <span class="ml-1 cursor-help text-blue-600">
   ?
  </span>
 </label>
 <input class="form-input w-full" id="pattern" name="pattern" type="text"/>
</div>
```

For now this field can be ignored in backend unless defined later in the spec.

---

### 🛠️ Modifiers

Rule presets added by user interaction. These should toggle behind-the-scenes rule files applied to the dictionary.

```html
<div class="mb-4">
 <label class="block text-sm font-medium text-gray-900 dark:text-white">
  Modifiers
 </label>
 <div class="flex flex-wrap gap-2 mt-2">
  <button class="btn btn-link" type="button">
   + Change case
  </button>
  <button class="btn btn-link" type="button">
   + Change chars order
  </button>
  <button class="btn btn-link" type="button">
   + Substitute chars
  </button>
 </div>
</div>
```

Each modifier button acts as a dropdown that allows it to add several modifiers that are specific to the modifier type. The types are listed below.

Change case:

- Uppercase (adds the rule `u`)
- Lowercase (adds the rule `l`)
- Capitalize (adds the rule `c`)
- Toggle case (adds the rule `t`)

Change chars order:

- Duplicate (adds the rule `d`)
- Reverse (adds the rule `r`)

Substitute chars: _This copies rules from several predefined lists collected from hashcat._

- Substitute Leetspeak (adds the rules from `rules/unix-ninja-leetspeak.rule`)
- Substitute with Combinator (adds the rules from `rules/combinator.rule`)

---

### 📊 Passwords & Complexity

```html
<div class="mt-4 text-sm text-gray-900 dark:text-white">
 <p>
  <strong>
   Passwords to check:
  </strong>
  198
 </p>
 <p>
  <strong>
   Complexity:
  </strong>
  <span class="inline-flex space-x-1">
   <span class="w-2 h-2 bg-gray-400 rounded-full">
   </span>
   <span class="w-2 h-2 bg-gray-400 rounded-full">
   </span>
   <span class="w-2 h-2 bg-gray-400 rounded-full">
   </span>
   <span class="w-2 h-2 bg-gray-400 rounded-full">
   </span>
   <span class="w-2 h-2 bg-gray-400 rounded-full">
   </span>
  </span>
 </p>
</div>
```

Use `POST /api/v1/web/attacks/estimate` to compute updated password count + complexity based on dictionary + rule modifiers.

---

### ✅ Footer Buttons

```html
<div class="flex justify-end space-x-2 mt-6">
 <button class="btn btn-outline" data-modal-hide="dictionaryModal" type="button">
  Cancel
 </button>
 <button class="btn btn-primary" type="submit">
  Add Attack
 </button>
</div>
```

---

### 📦 Backend Submission Notes

```jsonc
{
    "attack_mode": "dictionary",
    "attack_mode_hashcat": 0,
    "word_list_id": "xyz123", // maps to selected AttackResourceFile
    "min_length": 1,
    "max_length": 128,
    "rule_list_id": "<optional>", // if modifiers selected
    "pattern": "" // optional
}
```

The rule_list_id should reference an ephemeral AttackResourceFile of type EPHEMERAL_RULE_LIST.
