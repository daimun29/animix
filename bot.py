# Mekanik mixing bawaan hanya untuk Panda (102) dan Harimau (103)
self.log("🔄 Mixing remaining DNA (Panda with Tiger only)...", Fore.CYAN)
panda_dna = None
tiger_dna = None

# Cari Panda dan Harimau di dna_list
for dna in dna_list:
    if dna["item_id"] in used_ids:
        continue
    if str(dna.get("dna_id")) == "102":  # Panda DNA
        panda_dna = dna
    elif str(dna.get("dna_id")) == "103":  # Tiger DNA
        tiger_dna = dna
    if panda_dna and tiger_dna:
        break

# Jika Panda dan Harimau ditemukan, gabungkan
if panda_dna and tiger_dna and tiger_dna["can_mom"]:
    payload = {"dad_id": panda_dna["item_id"], "mom_id": tiger_dna["item_id"]}
    self.log(
        f"🔄 Mixing Panda (Item ID: {panda_dna['item_id']}) with Tiger (Item ID: {tiger_dna['item_id']})...",
        Fore.CYAN,
    )
    while True:
        try:
            mix_response = requests.post(
                mix_url, headers=headers, json=payload, timeout=10
            )
            if mix_response.status_code == 200:
                mix_data = mix_response.json()
                if "result" in mix_data and "pet" in mix_data["result"]:
                    pet_info = mix_data["result"]["pet"]
                    self.log(
                        f"🎉 New pet created: {pet_info['name']} (ID: {pet_info['pet_id']})",
                        Fore.GREEN,
                    )
                    used_ids.add(panda_dna["item_id"])
                    used_ids.add(tiger_dna["item_id"])
                    break
                else:
                    message = mix_data.get("message", "No message provided.")
                    self.log(
                        f"⚠️ Mixing failed for Panda {panda_dna['item_id']}, Tiger {tiger_dna['item_id']}: {message}",
                        Fore.YELLOW,
                    )
                    break
            elif mix_response.status_code == 429:
                self.log(
                    "⏳ Too many requests (429). Retrying in 5 seconds...",
                    Fore.YELLOW,
                )
                time.sleep(5)
            else:
                self.log(
                    f"❌ Request failed for Panda {panda_dna['item_id']}, Tiger {tiger_dna['item_id']} (Status: {mix_response.status_code})",
                    Fore.RED,
                )
                break
        except requests.exceptions.RequestException as e:
            self.log(
                f"❌ Request failed for Panda {panda_dna['item_id']}, Tiger {tiger_dna['item_id']}: {e}",
                Fore.RED,
            )
            break
else:
    self.log("⚠️ Panda or Tiger DNA not found or unavailable for mixing.", Fore.YELLOW)
