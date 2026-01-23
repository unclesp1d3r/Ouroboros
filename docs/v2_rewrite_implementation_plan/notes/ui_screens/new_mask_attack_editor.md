## Page: New Mask Attack Dialog

This modal form allows a user to define a new **Mask-based attack**, including optional mask files, inline mask definitions, and custom symbol sets.

### TIP: Summary

- Rendered as a Flowbite modal
- HTMX form post to `/api/v1/web/attacks/`
- Allows upload of a mask file _or_ inline masks
- Supports up to four custom charsets (`?1`, `?2`, `?3`, `?4`)
- Dynamically displays the total keyspace and complexity meter
- Includes "modificators" UI (optional rule-based transformations)

---

### Modal Header

```html
<h3 class="text-xl font-bold text-gray-900 dark:text-white">
 New Mask Attack
</h3>
<p class="text-sm text-gray-500 dark:text-gray-400">
 Mask Attack checks passwords that match a specified pattern or mask.
</p>
```

---

### Mask File Upload (Optional)

```html
<div class="mb-4">
 <label class="block text-sm font-medium text-gray-900 dark:text-white" for="mask_file">
  Mask File (optional)
 </label>
 <input class="file-input w-full" id="mask_file" name="mask_file" type="file"/>
</div>
```

---

### Language Selector

```html
<div class="mb-4">
 <label class="block text-sm font-medium text-gray-900 dark:text-white" for="language">
  Language
 </label>
 <select class="form-select w-full" id="language" name="language">
  <option value="english">
   English
  </option>
  <!-- Add other languages as needed -->
 </select>
</div>
```

---

### 🔣 Inline Mask Entry

```html
<div class="mb-4">
 <label class="block text-sm font-medium text-gray-900 dark:text-white" for="masks">
  Masks
 </label>
 <div class="flex gap-2">
  <input class="form-input w-full" name="masks[]" type="text" value="?u?1?1?d?d?dPhotos?s"/>
  <button class="btn btn-outline text-red-600" type="button">
   ✕
  </button>
 </div>
 <button class="btn btn-link mt-2" type="button">
  + Add Mask
 </button>
</div>
```

---

### Custom Symbol Sets

These correspond to `?1` to `?4` in mask syntax. Shown as a vertical list.

```html
<div class="mb-4">
 <label class="block text-sm font-medium text-gray-900 dark:text-white">
  Custom Symbol Sets
 </label>
 <div class="space-y-2">
  <input class="form-input w-full" name="custom_charset_1" placeholder="Set 1 (e.g., 12)" type="text" value="12"/>
  <input class="form-input w-full" name="custom_charset_2" placeholder="Set 2" type="text"/>
  <input class="form-input w-full" name="custom_charset_3" placeholder="Set 3" type="text"/>
  <input class="form-input w-full" name="custom_charset_4" placeholder="Set 4" type="text"/>
 </div>
</div>
```

---

### Modificators (Optional Rule-Like Transforms)

These are UI buttons that translate into rule file presets on the backend.

```html
<div class="mb-4">
 <label class="block text-sm font-medium text-gray-900 dark:text-white">
  Modificators
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

Skirmish should convert these buttons into one or more rule files applied during attack construction, and store them in the `rule_list` field internally.

---

### Keyspace & Complexity

```html
<div class="mt-4 text-sm text-gray-900 dark:text-white">
 <p>
  <strong>
   Passwords to check:
  </strong>
  44,616,000
 </p>
 <p>
  <strong>
   Complexity:
  </strong>
  <span class="inline-flex space-x-1">
   <span class="w-2 h-2 bg-green-500 rounded-full">
   </span>
   <span class="w-2 h-2 bg-green-500 rounded-full">
   </span>
   <span class="w-2 h-2 bg-green-500 rounded-full">
   </span>
   <span class="w-2 h-2 bg-gray-400 rounded-full">
   </span>
   <span class="w-2 h-2 bg-gray-400 rounded-full">
   </span>
  </span>
 </p>
</div>
```

These values should be computed server-side via a call to: `POST /api/v1/web/attacks/estimate`\
with live updates triggered via `hx-trigger="change"` from any input field.

---

### [x] Buttons (Footer)

```html
<div class="flex justify-end gap-2 mt-6">
 <button class="btn btn-outline" data-modal-hide="maskAttackModal" type="button">
  Cancel
 </button>
 <button class="btn btn-primary" type="submit">
  Add Attack
 </button>
</div>
```

---

### Backend Submission Notes

Skirmish should post this attack with the following fields:

```jsonc
{
    "attack_mode": "mask",
    "attack_mode_hashcat": 3,
    "increment_mode": false,
    "mask_list": ["?u?1?1?d?d?dPhotos?s"],
    "custom_charset_1": "12",
    "custom_charset_2": "",
    "custom_charset_3": "",
    "custom_charset_4": "",
    "rule_list_id": "<optional: if any modificator is selected>"
}
```
