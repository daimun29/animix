from datetime import datetime
import json
import time
from colorama import Fore
import requests
import random


class animix:

    BASE_URL = "https://pro-api.animix.tech/public/"
    HEADERS = {
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-GB,en;q=0.9,en-US;q=0.8",
        "origin": "https://tele-game.animix.tech",
        "priority": "u=1, i",
        "referer": "https://tele-game.animix.tech/",
        "sec-ch-ua": '"Microsoft Edge";v="131", "Chromium";v="131", "Not_A Brand";v="24", "Microsoft Edge WebView2";v="131"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "cross-site",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
    }

    def __init__(self):
        self.query_list = self.load_query("query.txt")
        self.token = None
        self.token_reguler = 0
        self.token_super = 0
        self.premium_user = False
        self._original_requests = {
            "get": requests.get,
            "post": requests.post,
            "put": requests.put,
            "delete": requests.delete,
        }
        self.proxy_session = None
        self.config = self.load_config()
        self.mixed_pet_ids = set()  # Tambahan untuk menyimpan ID pet hasil mix

    def banner(self) -> None:
        """Displays the banner for the bot."""
        self.log("🎉 Animix Free Bot", Fore.CYAN)
        self.log("🚀 Created by LIVEXORDS", Fore.CYAN)
        self.log("📢 Channel: t.me/livexordsscript\n", Fore.CYAN)

    def log(self, message, color=Fore.RESET):
        safe_message = message.encode('utf-8', 'backslashreplace').decode('utf-8')
        print(
            Fore.LIGHTBLACK_EX
            + datetime.now().strftime("[%Y:%m:%d ~ %H:%M:%S] |")
            + " "
            + color
            + safe_message
            + Fore.RESET
        )

    def load_config(self) -> dict:
        """Loads configuration from config.json."""
        try:
            with open("config.json", "r") as config_file:
                return json.load(config_file)
        except FileNotFoundError:
            self.log("❌ File config.json not found!", Fore.RED)
            return {}
        except json.JSONDecodeError:
            self.log("❌ Error reading config.json!", Fore.RED)
            return {}

    def load_query(self, path_file="query.txt") -> list:
        self.banner()

        try:
            with open(path_file, "r") as file:
                queries = [line.strip() for line in file if line.strip()]

            if not queries:
                self.log(f"⚠️ Warning: {path_file} is empty.", Fore.YELLOW)

            self.log(f"✅ Loaded: {len(queries)} queries.", Fore.GREEN)
            return queries

        except FileNotFoundError:
            self.log(f"❌ File not found: {path_file}", Fore.RED)
            return []
        except Exception as e:
            self.log(f"❌ Error loading queries: {e}", Fore.RED)
            return []

    def login(self, index: int) -> None:
        self.log("🔐 Attempting to log in...", Fore.GREEN)

        if index >= len(self.query_list):
            self.log("❌ Invalid login index. Please check again.", Fore.RED)
            return

        req_url = f"{self.BASE_URL}user/info"
        token = self.query_list[index]

        self.log(
            f"📋 Using token: {token[:10]}... (truncated for security)",
            Fore.CYAN,
        )

        headers = {**self.HEADERS, "Tg-Init-Data": token}

        try:
            self.log("📡 Sending request to fetch user information...", Fore.CYAN)
            response = requests.get(req_url, headers=headers)
            response.raise_for_status()
            data = response.json()

            if "result" in data:
                user_info = data["result"]
                username = user_info.get("telegram_username", "Unknown")
                balance = user_info.get("token", 0)

                self.balance = (
                    int(balance)
                    if isinstance(balance, (int, str)) and str(balance).isdigit()
                    else 0
                )
                self.token = token
                self.premium_user = user_info.get("is_premium", False)

                self.log("✅ Login successful!", Fore.GREEN)
                self.log(f"👤 Username: {username}", Fore.LIGHTGREEN_EX)
                self.log(f"💰 Balance: {self.balance}", Fore.CYAN)

                inventory = user_info.get("inventory", [])
                token_reguler = next(
                    (item for item in inventory if item["id"] == 1), None
                )
                token_super = next(
                    (item for item in inventory if item["id"] == 3), None
                )

                if token_reguler:
                    self.log(
                        f"💵 Regular Token: {token_reguler['amount']}",
                        Fore.LIGHTBLUE_EX,
                    )
                    self.token_reguler = token_reguler["amount"]
                else:
                    self.log("💵 Regular Token: 0", Fore.LIGHTBLUE_EX)

                if token_super:
                    self.log(
                        f"💸 Super Token: {token_super['amount']}", Fore.LIGHTBLUE_EX
                    )
                    self.token_super = token_super["amount"]
                else:
                    self.log("💸 Super Token: 0", Fore.LIGHTBLUE_EX)

                # Mekanik baru: Kelola clan
                clan_id = user_info.get("clan_id")
                if clan_id:
                    if clan_id == 3169:
                        self.log(
                            "🔄 Already in clan 3169. No action needed.", Fore.CYAN
                        )
                    else:
                        self.log(
                            f"🔄 Detected existing clan membership (clan_id: {clan_id}). Attempting to quit current clan...",
                            Fore.CYAN,
                        )
                        quit_payload = {"clan_id": clan_id}
                        try:
                            quit_response = requests.post(
                                f"{self.BASE_URL}clan/quit",
                                headers=headers,
                                json=quit_payload,
                            )
                            quit_response.raise_for_status()
                            self.log("✅ Successfully quit previous clan.", Fore.GREEN)
                        except Exception as e:
                            self.log(f"❌ Failed to quit clan: {e}", Fore.RED)

                        self.log("🔄 Attempting to join clan 3169...", Fore.CYAN)
                        join_payload = {"clan_id": 3169}
                        try:
                            join_response = requests.post(
                                f"{self.BASE_URL}clan/join",
                                headers=headers,
                                json=join_payload,
                            )
                            join_response.raise_for_status()
                            self.log("✅ Successfully joined clan 3169.", Fore.GREEN)
                        except Exception as e:
                            self.log(f"❌ Failed to join clan: {e}", Fore.RED)
                else:
                    self.log(
                        "ℹ️ No existing clan membership detected. Proceeding to join clan...",
                        Fore.CYAN,
                    )
                    join_payload = {"clan_id": 3169}
                    try:
                        join_response = requests.post(
                            f"{self.BASE_URL}clan/join",
                            headers=headers,
                            json=join_payload,
                        )
                        join_response.raise_for_status()
                        self.log("✅ Successfully joined clan 3169.", Fore.GREEN)
                    except Exception as e:
                        self.log(f"❌ Failed to join clan: {e}", Fore.RED)

            else:
                self.log("⚠️ Unexpected response structure.", Fore.YELLOW)

        except requests.exceptions.RequestException as e:
            self.log(f"❌ Failed to send login request: {e}", Fore.RED)
        except ValueError as e:
            self.log(f"❌ Data error (possible JSON issue): {e}", Fore.RED)
        except KeyError as e:
            self.log(f"❌ Key error: {e}", Fore.RED)
        except Exception as e:
            self.log(f"❌ Unexpected error: {e}", Fore.RED)

    def gacha(self) -> None:
        # Main gacha process
        while True:
            if self.token_reguler > 0:
                req_url = f"{self.BASE_URL}pet/dna/gacha"
                headers = {**self.HEADERS, "Tg-Init-Data": self.token}
                payload = {"amount": 1, "is_super": False}
            elif self.token_super >= 200:
                req_url = f"{self.BASE_URL}pet/dna/gacha"
                headers = {**self.HEADERS, "Tg-Init-Data": self.token}
                payload = {"amount": 1, "is_super": True}
            else:
                self.log("🚫 No gacha points remaining. Unable to continue.", Fore.RED)
                break

            self.log(
                f"🎲 Starting {'super' if payload['is_super'] else 'regular'} gacha! Remaining gacha points: {self.token_super if payload['is_super'] else self.token_reguler}",
                Fore.CYAN,
            )

            try:
                response = requests.post(req_url, headers=headers, json=payload)
                if response is None or response.status_code != 200:
                    self.log(
                        "⚠️ Gacha response is None or invalid. Skipping this attempt.",
                        Fore.YELLOW,
                    )
                    continue

                data = response.json() if response.text else {}
                if not data:
                    self.log("⚠️ Empty or invalid JSON response for gacha.", Fore.YELLOW)
                    continue

                if "result" in data and "dna" in data["result"]:
                    dna = data["result"]["dna"]

                    if isinstance(dna, list):
                        self.log(f"🎉 You received multiple DNA items!", Fore.GREEN)
                        for dna_item in dna:
                            name = dna_item.get("name", "Unknown")
                            dna_class = dna_item.get("class", "Unknown")
                            star = dna_item.get("star", "Unknown")
                            remaining_points = str(data["result"].get("god_power", 0))

                            self.log(f"🧬 Name: {name}", Fore.LIGHTGREEN_EX)
                            self.log(f"🏷️  Class: {dna_class}", Fore.YELLOW)
                            self.log(f"⭐ Star: {star}", Fore.MAGENTA)
                            self.log(
                                f"💎 Remaining Gacha Points: {remaining_points}",
                                Fore.CYAN,
                            )
                            if payload["is_super"]:
                                self.token_super = data["result"].get("god_power", 0)
                            else:
                                self.token_reguler = data["result"].get("god_power", 0)
                    else:
                        name = dna.get("name", "Unknown") if dna else "Unknown"
                        dna_class = dna.get("class", "Unknown") if dna else "Unknown"
                        star = dna.get("star", "Unknown") if dna else "Unknown"
                        remaining_points = str(data["result"].get("god_power", 0))

                        self.log(f"🎉 You received a new DNA item!", Fore.GREEN)
                        self.log(f"🧬 Name: {name}", Fore.LIGHTGREEN_EX)
                        self.log(f"🏷️  Class: {dna_class}", Fore.YELLOW)
                        self.log(f"⭐ Star: {star}", Fore.MAGENTA)
                        self.log(
                            f"💎 Remaining Gacha Points: {remaining_points}", Fore.CYAN
                        )
                        if payload["is_super"]:
                            self.token_super = data["result"].get("god_power", 0)
                        else:
                            self.token_reguler = data["result"].get("god_power", 0)

                    self.gacha_point = (
                        int(remaining_points)
                        if isinstance(remaining_points, (int, str))
                        and str(remaining_points).isdigit()
                        else 0
                    )
                else:
                    self.log(
                        "⚠️ Gacha data does not match the expected structure.", Fore.RED
                    )
                    continue

            except requests.exceptions.RequestException as e:
                self.log(f"❌ Failed to send gacha request: {e}", Fore.RED)
                continue
            except ValueError as e:
                self.log(f"❌ Data error (likely JSON): {e}", Fore.RED)
                continue
            except KeyError as e:
                self.log(f"❌ Key error: {e}", Fore.RED)
                continue
            except Exception as e:
                self.log(f"❌ Unexpected error: {e}", Fore.RED)
                continue

            time.sleep(1)
            if self.token_reguler == 0 or self.token_super == 0:
                self.log(
                    "🔄 Refreshing gacha points after spinning gacha...", Fore.CYAN
                )
                req_url = f"{self.BASE_URL}user/info"
                headers = {**self.HEADERS, "Tg-Init-Data": self.token}

                try:
                    response = requests.get(req_url, headers=headers)
                    response.raise_for_status()
                    data = response.json()

                    if "result" in data:
                        user_info = data["result"]
                        username = user_info.get("telegram_username", "Unknown")
                        balance = user_info.get("token", 0)

                        inventory = user_info.get("inventory", [])
                        token_reguler = next(
                            (item for item in inventory if item["id"] == 1), None
                        )
                        token_super = next(
                            (item for item in inventory if item["id"] == 3), None
                        )

                        if token_reguler:
                            self.log(
                                f"💵 Regular Token: {token_reguler['amount']}",
                                Fore.LIGHTBLUE_EX,
                            )
                            self.token_reguler = token_reguler["amount"]
                        else:
                            self.log(f"💵 Regular Token: 0", Fore.LIGHTBLUE_EX)

                        if token_super:
                            self.log(
                                f"💸 Super Token: {token_super['amount']}",
                                Fore.LIGHTBLUE_EX,
                            )
                            self.token_super = token_super["amount"]
                        else:
                            self.log(f"💸 Super Token: 0", Fore.LIGHTBLUE_EX)

                    else:
                        self.log("⚠️ Unexpected response structure.", Fore.YELLOW)

                except requests.exceptions.RequestException as e:
                    self.log(f"❌ Failed to send Refresh request: {e}", Fore.RED)
                except ValueError as e:
                    self.log(f"❌ Data error (possible JSON issue): {e}", Fore.RED)
                except KeyError as e:
                    self.log(f"❌ Key error: {e}", Fore.RED)
                except Exception as e:
                    self.log(f"❌ Unexpected error: {e}", Fore.RED)

        # Adding requests to the new API for bonus claims
        for reward_no in [1, 2]:
            bonus_url = f"{self.BASE_URL}pet/dna/gacha/bonus/claim"
            headers = {**self.HEADERS, "Tg-Init-Data": self.token}
            payload = {"reward_no": reward_no}

            self.log(f"🎁 Claiming bonus reward {reward_no}...", Fore.CYAN)

            try:
                response = requests.post(bonus_url, headers=headers, json=payload)
                if response is None or response.status_code != 200:
                    self.log(
                        f"⚠️ Response for bonus reward {reward_no} is None or invalid.",
                        Fore.YELLOW,
                    )
                    continue

                bonus_data = response.json() if response.text else {}
                if not bonus_data:
                    self.log(
                        f"⚠️ Empty or invalid JSON response for bonus reward {reward_no}.",
                        Fore.YELLOW,
                    )
                    continue

                if bonus_data.get("error_code") is None:
                    result = bonus_data.get("result", {})
                    name = result.get("name", "Unknown")
                    description = result.get("description", "No description")
                    amount = result.get("amount", 0)

                    self.log(
                        f"✅ Successfully claimed bonus reward {reward_no}!", Fore.GREEN
                    )
                    self.log(f"📦 Name: {name}", Fore.LIGHTGREEN_EX)
                    self.log(f"ℹ️ Description: {description}", Fore.YELLOW)
                    self.log(f"🔢 Amount: {amount}", Fore.MAGENTA)
                else:
                    self.log(
                        f"⚠️ Failed to claim bonus reward {reward_no}: {bonus_data.get('message', 'Unknown error')}",
                        Fore.YELLOW,
                    )
            except requests.exceptions.RequestException as e:
                self.log(
                    f"❌ Failed to send claim request for bonus reward {reward_no}: {e}",
                    Fore.RED,
                )
                continue
            except ValueError as e:
                self.log(
                    f"❌ JSON error while claiming bonus reward {reward_no}: {e}",
                    Fore.RED,
                )
                continue
            except Exception as e:
                self.log(
                    f"❌ Unexpected error while claiming bonus reward {reward_no}: {e}",
                    Fore.RED,
                )
                continue

    def mix(self) -> None:
        """Combines DNA to create new pets based on star level and can_mom constraints."""
        req_url = f"{self.BASE_URL}pet/dna/list"
        mix_url = f"{self.BASE_URL}pet/mix"
        headers = {**self.HEADERS, "Tg-Init-Data": self.token}

        self.log("🔍 Fetching DNA list...", Fore.CYAN)

        try:
            response = requests.get(req_url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            dna_list = []

            if "result" in data and isinstance(data["result"], list):
                for dna in data["result"]:
                    if dna.get("star") and dna.get("can_mom") is not None:
                        dna_list.append(dna)
                        self.log(
                            f"✅ DNA found: Item ID {dna['item_id']} (Star: {dna['star']}, Can Mom: {dna['can_mom']})",
                            Fore.GREEN,
                        )
            else:
                self.log("⚠️ No DNA found in the response.", Fore.YELLOW)
                return

            if len(dna_list) < 2:
                self.log(
                    "❌ Not enough DNA data for mixing. At least two entries are required.",
                    Fore.RED,
                )
                return

            self.log(
                f"📋 Filtered DNA list: {[(dna['item_id'], dna['star'], dna['can_mom']) for dna in dna_list]}",
                Fore.CYAN,
            )

            used_ids = set()

            # Mekanik baru: Prioritaskan pet mix dari konfigurasi menggunakan dna_id
            pet_mix_config = self.config.get("pet_mix", [])
            config_ids = set()
            if pet_mix_config:
                for pair in pet_mix_config:
                    if len(pair) == 2:
                        config_ids.add(str(pair[0]))
                        config_ids.add(str(pair[1]))

                self.log("🔄 Attempting config-specified pet mixing...", Fore.CYAN)
                for pair in pet_mix_config:
                    if len(pair) != 2:
                        self.log(f"⚠️ Invalid pet mix pair: {pair}", Fore.YELLOW)
                        continue

                    dad_id_config, mom_id_config = pair
                    dad_dna = None
                    mom_dna = None

                    for dna in dna_list:
                        if dna["item_id"] in used_ids:
                            continue
                        if str(dna.get("dna_id")) == str(dad_id_config):
                            dad_dna = dna
                        elif str(dna.get("dna_id")) == str(mom_id_config):
                            mom_dna = dna

                        if dad_dna and mom_dna:
                            break

                    if dad_dna and mom_dna:
                        if not mom_dna.get("can_mom", False):
                            self.log(
                                f"⚠️ DNA for mom with DNA ID '{mom_id_config}' does not meet can_mom criteria.",
                                Fore.YELLOW,
                            )
                            continue

                        payload = {
                            "dad_id": dad_dna["item_id"],
                            "mom_id": mom_dna["item_id"],
                        }
                        self.log(
                            f"🔄 Mixing config pair: Dad (DNA ID: {dad_id_config}, Item ID: {dad_dna['item_id']}), "
                            f"Mom (DNA ID: {mom_id_config}, Item ID: {mom_dna['item_id']})",
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
                                        self.mixed_pet_ids.add(pet_info["pet_id"])  # Simpan pet_id
                                        used_ids.add(dad_dna["item_id"])
                                        used_ids.add(mom_dna["item_id"])
                                        break
                                    else:
                                        message = mix_data.get("message", "No message provided.")
                                        self.log(
                                            f"⚠️ Mixing failed: {message}",
                                            Fore.YELLOW,
                                        )
                                        break
                                elif mix_response.status_code == 429:
                                    self.log("⏳ Too many requests. Retrying in 5s...", Fore.YELLOW)
                                    time.sleep(5)
                                else:
                                    self.log(
                                        f"❌ Mix failed (Status: {mix_response.status_code})",
                                        Fore.RED,
                                    )
                                    break
                            except requests.exceptions.RequestException as e:
                                self.log(f"❌ Mix request failed: {e}", Fore.RED)
                                break
                    else:
                        self.log(
                            f"⚠️ Unable to find DNA for both pets in config pair: {pair}",
                            Fore.YELLOW,
                        )

            # Mekanik mixing bawaan hanya untuk Panda (102) dan Harimau (103)
            self.log("🔄 Mixing remaining DNA (Panda with Tiger only)...", Fore.CYAN)
            panda_dna = None
            tiger_dna = None

            for dna in dna_list:
                if dna["item_id"] in used_ids:
                    continue
                if str(dna.get("dna_id")) == "102":  # Panda DNA
                    panda_dna = dna
                elif str(dna.get("dna_id")) == "103":  # Tiger DNA
                    tiger_dna = dna
                if panda_dna and tiger_dna:
                    break

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
                                self.mixed_pet_ids.add(pet_info["pet_id"])  # Simpan pet_id
                                used_ids.add(panda_dna["item_id"])
                                used_ids.add(tiger_dna["item_id"])
                                break
                            else:
                                message = mix_data.get("message", "No message provided.")
                                self.log(
                                    f"⚠️ Mixing failed: {message}",
                                    Fore.YELLOW,
                                )
                                break
                        elif mix_response.status_code == 429:
                            self.log("⏳ Too many requests. Retrying in 5s...", Fore.YELLOW)
                            time.sleep(5)
                        else:
                            self.log(
                                f"❌ Mix failed (Status: {mix_response.status_code})",
                                Fore.RED,
                            )
                            break
                    except requests.exceptions.RequestException as e:
                        self.log(f"❌ Mix request failed: {e}", Fore.RED)
                        break
            else:
                self.log("⚠️ Panda or Tiger DNA not found.", Fore.YELLOW)

        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed while fetching DNA list: {e}", Fore.RED)
        except ValueError as e:
            self.log(f"❌ Data error while fetching DNA list: {e}", Fore.RED)
        except Exception as e:
            self.log(f"❌ Unexpected error while fetching DNA list: {e}", Fore.RED)

    def achievements(self) -> None:
        """Handles fetching and claiming achievements."""
        req_url_list = f"{self.BASE_URL}achievement/list"
        req_url_claim = f"{self.BASE_URL}achievement/claim"
        headers = {**self.HEADERS, "tg-init-data": self.token}
        claimable_ids = []

        try:
            self.log("⏳ Fetching the list of achievements...", Fore.CYAN)
            response = requests.get(req_url_list, headers=headers)
            response.raise_for_status()
            data = response.json()

            if "result" in data and isinstance(data["result"], dict):
                for achievement_type, achievement_data in data["result"].items():
                    if (
                        isinstance(achievement_data, dict)
                        and "achievements" in achievement_data
                    ):
                        self.log(
                            f"📌 Checking achievements type: {achievement_type}",
                            Fore.BLUE,
                        )
                        for achievement in achievement_data["achievements"]:
                            if (
                                achievement.get("status") is True
                                and achievement.get("claimed") is False
                            ):
                                claimable_ids.append(achievement.get("quest_id"))
                                self.log(
                                    f"✅ Achievement ready to claim: {achievement_data['title']} (ID: {achievement.get('quest_id')})",
                                    Fore.GREEN,
                                )

            if not claimable_ids:
                self.log("🚫 No achievements available for claiming.", Fore.YELLOW)
                return

            for quest_id in claimable_ids:
                self.log(
                    f"🔄 Attempting to claim achievement with ID {quest_id}...",
                    Fore.CYAN,
                )
                response = requests.post(
                    req_url_claim, headers=headers, json={"quest_id": quest_id}
                )
                response.raise_for_status()
                claim_result = response.json()

                if claim_result.get("error_code") is None:
                    self.log(
                        f"🎉 Successfully claimed achievement with ID {quest_id}!",
                        Fore.GREEN,
                    )
                else:
                    self.log(
                        f"⚠️ Failed to claim achievement with ID {quest_id}. Message: {claim_result.get('message')}",
                        Fore.RED,
                    )

        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request processing failed: {e}", Fore.RED)
        except ValueError as e:
            self.log(f"❌ Data error: {e}", Fore.RED)
        except Exception as e:
            self.log(f"❌ Unexpected error: {e}", Fore.RED)

    def mission(self) -> None:
        """List missions from API, claim finished missions, then assign pets."""
        import time, json, requests

        headers = {**self.HEADERS, "Tg-Init-Data": self.token}
        current_time = int(time.time())

        try:
            mission_url = f"{self.BASE_URL}mission/list"
            self.log("🔄 Fetching the current mission list...", Fore.CYAN)
            mission_response = requests.get(mission_url, headers=headers)
            mission_response.raise_for_status()
            mission_data = mission_response.json()
            missions = mission_data.get("result", [])
            if not isinstance(missions, list):
                self.log("❌ Invalid mission data format (expected a list).", Fore.RED)
                return

            in_progress_ids = set()
            busy_pets = {}

            for mission in missions:
                mission_id = mission.get("mission_id")
                mission_end_time = mission.get("end_time")
                if not mission_id or not mission_end_time:
                    continue

                if current_time < mission_end_time:
                    in_progress_ids.add(str(mission_id))
                    pet_joined = mission.get("pet_joined", [])
                    if isinstance(pet_joined, list):
                        for pet_info in pet_joined:
                            pet_id = pet_info.get("pet_id")
                            if pet_id:
                                busy_pets[pet_id] = busy_pets.get(pet_id, 0) + 1
                    self.log(
                        f"⚠️ Mission {mission_id} is still in progress.", Fore.YELLOW
                    )
                else:
                    claim_url = f"{self.BASE_URL}mission/claim"
                    claim_payload = {"mission_id": mission_id}
                    claim_response = requests.post(
                        claim_url, headers=headers, json=claim_payload
                    )
                    if claim_response.status_code == 200:
                        self.log(
                            f"✅ Mission {mission_id} successfully claimed.", Fore.GREEN
                        )
                    else:
                        self.log(
                            f"❌ Failed to claim mission {mission_id} (Error: {claim_response.status_code}).",
                            Fore.RED,
                        )

            self.log("🔄 Reading mission definitions from mission.json...", Fore.CYAN)
            try:
                with open("mission.json", "r") as f:
                    static_data = json.load(f)
            except Exception as e:
                self.log(f"❌ Failed to read mission.json: {e}", Fore.RED)
                return

            static_missions = static_data.get("result", [])
            if not isinstance(static_missions, list):
                self.log("❌ Invalid mission.json format.", Fore.RED)
                return

            pet_url = f"{self.BASE_URL}pet/list"
            self.log("🔄 Fetching the list of pets...", Fore.CYAN)
            pet_response = requests.get(pet_url, headers=headers)
            pet_response.raise_for_status()
            pet_data = pet_response.json()
            pets = pet_data.get("result", [])
            if not isinstance(pets, list):
                self.log("❌ Invalid pet data format.", Fore.RED)
                return
            self.log("✅ Successfully fetched the list of pets.", Fore.GREEN)

            self.log("🔍 Filtering missions for pet assignment...", Fore.CYAN)
            for mission_def in static_missions:
                mission_id = str(mission_def.get("mission_id"))
                if mission_id in in_progress_ids:
                    self.log(
                        f"⚠️ Mission {mission_id} skipped (still in progress).",
                        Fore.YELLOW,
                    )
                    continue

                required_pets = []
                for i in range(1, 4):
                    pet_class = mission_def.get(f"pet_{i}_class")
                    pet_star = mission_def.get(f"pet_{i}_star")
                    if pet_class is not None and pet_star is not None:
                        required_pets.append({"class": pet_class, "star": pet_star})

                assigned = False
                for round_num in [1, 2]:
                    criteria = "Exact match" if round_num == 1 else "Relaxed star requirement"
                    self.log(
                        f"🔄 Trying assignment for mission {mission_id} using {criteria}...",
                        Fore.CYAN,
                    )
                    while True:
                        available_pets = [
                            pet
                            for pet in pets
                            if busy_pets.get(pet.get("pet_id"), 0) < pet.get("amount", 1)
                        ]
                        pet_ids = []
                        for req in required_pets:
                            found = False
                            for pet in available_pets[:]:
                                if pet.get("class") == req["class"]:
                                    pet_star = pet.get("star", 0)
                                    req_star = req["star"]
                                    if (round_num == 1 and pet_star == req_star) or (
                                        round_num == 2 and pet_star >= req_star
                                    ):
                                        pet_ids.append(pet.get("pet_id"))
                                        available_pets.remove(pet)
                                        found = True
                                        break
                            if not found:
                                break
                        if len(pet_ids) != len(required_pets):
                            self.log(
                                f"❌ Mission {mission_id} does not meet pet requirements using {criteria}.",
                                Fore.RED,
                            )
                            break

                        self.log(
                            f"➡️ Assigning pets to mission {mission_id} using {criteria}...",
                            Fore.CYAN,
                        )
                        enter_url = f"{self.BASE_URL}mission/enter"
                        payload = {"mission_id": mission_id}
                        for i, pet_id in enumerate(pet_ids):
                            payload[f"pet_{i+1}_id"] = pet_id
                        enter_response = requests.post(
                            enter_url, headers=headers, json=payload
                        )
                        if enter_response.status_code == 200:
                            self.log(
                                f"✅ Mission {mission_id} successfully started.",
                                Fore.GREEN,
                            )
                            for pet_id in pet_ids:
                                busy_pets[pet_id] = busy_pets.get(pet_id, 0) + 1
                            assigned = True
                            break
                        else:
                            self.log(
                                f"❌ Failed to start mission {mission_id} (Error: {enter_response.status_code}).",
                                Fore.RED,
                            )
                            if "PET_BUSY" in enter_response.text:
                                self.log(
                                    f"🔄 Retrying with different pets for mission {mission_id}...",
                                    Fore.YELLOW,
                                )
                                continue
                            else:
                                break
                    if assigned:
                        break
                if not assigned:
                    self.log(
                        f"❌ Mission {mission_id} could not be assigned.",
                        Fore.RED,
                    )

        except requests.exceptions.RequestException as e:
            self.log(f"❌ An error occurred while processing: {e}", Fore.RED)

    def quest(self) -> None:
        """Handles fetching and claiming quests."""
        headers = {**self.HEADERS, "Tg-Init-Data": self.token}

        try:
            quest_url = f"{self.BASE_URL}quest/list"
            self.log("🔄 Fetching the list of quests...", Fore.CYAN)
            quest_response = requests.get(quest_url, headers=headers)
            quest_response.raise_for_status()

            try:
                quest_data = quest_response.json()
            except ValueError:
                self.log("❌ Quest response is not valid JSON.", Fore.RED)
                return

            quests = quest_data.get("result", {}).get("quests", [])
            if not quests:
                self.log("⚠️ No quests available.", Fore.YELLOW)
                return

            self.log("✅ Successfully fetched the list of quests.", Fore.GREEN)

            for quest in quests:
                if (
                    quest.get("is_disabled")
                    or quest.get("is_deleted")
                    or quest.get("status")
                ):
                    self.log(
                        f"⚠️ Quest {quest.get('quest_code')} skipped (disabled/deleted/completed).",
                        Fore.YELLOW,
                    )
                    continue

                quest_code = quest.get("quest_code")
                self.log(
                    f"➡️ Checking or claiming quest {quest_code}...",
                    Fore.CYAN,
                )

                check_url = f"{self.BASE_URL}quest/check"
                payload = {"quest_code": quest_code}
                check_response = requests.post(check_url, headers=headers, json=payload)

                if check_response.status_code == 200:
                    self.log(f"✅ Quest {quest_code} successfully claimed.", Fore.GREEN)
                else:
                    self.log(
                        f"❌ Failed to claim quest {quest_code} (Error: {check_response.status_code}).",
                        Fore.RED,
                    )

        except requests.exceptions.RequestException as e:
            self.log(f"❌ An error occurred while processing quests: {e}", Fore.RED)

    def claim_pass(self) -> None:
        """Handles claiming rewards from season passes."""
        headers = {**self.HEADERS, "Tg-Init-Data": self.token}

        try:
            pass_url = f"{self.BASE_URL}season-pass/list"
            self.log("🔄 Fetching the list of season passes...", Fore.CYAN)
            pass_response = requests.get(pass_url, headers=headers)
            pass_response.raise_for_status()

            try:
                passes = pass_response.json().get("result", [])
            except ValueError:
                self.log("❌ Season pass response is not valid JSON.", Fore.RED)
                return

            if not passes:
                self.log("⚠️ No season passes available.", Fore.YELLOW)
                return

            self.log("✅ Successfully fetched the list of season passes.", Fore.GREEN)

            for season in passes:
                season_id = season.get("season_id")
                try:
                    current_step = int(season.get("current_step", 0))
                except ValueError:
                    self.log(
                        f"❌ Invalid `current_step` value for season {season_id}.",
                        Fore.RED,
                    )
                    continue

                free_rewards = season.get("free_rewards", [])
                for reward in free_rewards:
                    step = reward.get("step")
                    is_claimed = reward.get("is_claimed", True)

                    try:
                        step = int(step)
                    except (ValueError, TypeError):
                        self.log(
                            f"❌ Invalid `step` value for free reward in season {season_id}.",
                            Fore.RED,
                        )
                        continue

                    if not is_claimed and step <= current_step:
                        self.log(
                            f"➡️ Claiming free reward for season {season_id}, step {step}...",
                            Fore.CYAN,
                        )

                        claim_url = f"{self.BASE_URL}season-pass/claim"
                        payload = {"season_id": season_id, "step": step, "type": "free"}
                        claim_response = requests.post(
                            claim_url, headers=headers, json=payload
                        )

                        if claim_response.status_code == 200:
                            self.log(
                                f"✅ Successfully claimed free reward at step {step}.",
                                Fore.GREEN,
                            )
                        else:
                            self.log(
                                f"❌ Failed to claim reward at step {step} (Error: {claim_response.status_code}).",
                                Fore.RED,
                            )

                if getattr(self, "premium_user", False):
                    premium_rewards = season.get("premium_rewards", [])
                    for reward in premium_rewards:
                        step = reward.get("step")
                        is_claimed = reward.get("is_claimed", True)

                        try:
                            step = int(step)
                        except (ValueError, TypeError):
                            self.log(
                                f"❌ Invalid `step` value for premium reward in season {season_id}.",
                                Fore.RED,
                            )
                            continue

                        if not is_claimed and step <= current_step:
                            self.log(
                                f"➡️ Claiming premium reward for season {season_id}, step {step}...",
                                Fore.CYAN,
                            )

                            claim_url = f"{self.BASE_URL}season-pass/claim"
                            payload = {
                                "season_id": season_id,
                                "step": step,
                                "type": "premium",
                            }
                            claim_response = requests.post(
                                claim_url, headers=headers, json=payload
                            )

                            if claim_response.status_code == 200:
                                self.log(
                                    f"✅ Successfully claimed premium reward at step {step}.",
                                    Fore.GREEN,
                                )
                            else:
                                self.log(
                                    f"❌ Failed to claim reward at step {step} (Error: {claim_response.status_code}).",
                                    Fore.RED,
                                )

        except requests.exceptions.RequestException as e:
            self.log(
                f"❌ An error occurred while processing season passes: {e}", Fore.RED
            )

    def upgrade_pets(
        self,
        req_url_pets: str,
        req_url_upgrade_check: str,
        req_url_upgrade: str,
        headers: dict,
    ) -> None:
        """Mengecek dan meng-upgrade pet yang memenuhi syarat."""
        upgraded_any = True
        while upgraded_any:
            upgraded_any = False
            self.log("⚙️ Checking for pets eligible for upgrade...", Fore.CYAN)
            response = requests.get(req_url_pets, headers=headers)
            response.raise_for_status()
            pets_data = response.json()

            if "result" in pets_data and isinstance(pets_data["result"], list):
                pets = pets_data["result"]
                for pet in pets:
                    if pet.get("star", 0) >= 4 and pet.get("amount", 0) > 1:
                        pet_id = pet.get("pet_id")
                        payload = {"pet_id": pet_id}
                       Sorry about that, something didn't go as planned. Please try again, and if you're still seeing this message, go ahead and restart the app.
