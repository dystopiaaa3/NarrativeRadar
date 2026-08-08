import os
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from dotenv import load_dotenv
from solders.pubkey import Pubkey


load_dotenv()


SOLANA_RPC = os.getenv(
    "SOLANA_RPC_URL",
    "https://api.mainnet-beta.solana.com"
)


class SolanaCollector:

    def __init__(self):

        self.rpc_url = SOLANA_RPC

        self.session = requests.Session()

        self.session.headers.update(
            {
                "Content-Type": "application/json"
            }
        )


    def _to_pubkey(
        self,
        address: str
    ):

        if not isinstance(address, str):
            raise ValueError(
                "Address must be a string"
            )

        address = address.strip()

        if not address:
            raise ValueError(
                "Address cannot be empty"
            )

        return Pubkey.from_string(
            address
        )


    def _rpc_request(
        self,
        method: str,
        params=None,
        timeout: int = 20
    ):

        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params or []
        }


        response = requests.post(
            self.rpc_url,
            json=payload,
            timeout=timeout,
            headers={
                "Content-Type": "application/json"
            }
        )


        response.raise_for_status()


        data = response.json()


        if "error" in data:

            error = data[
                "error"
            ]

            raise RuntimeError(
                f"RPC error "
                f"{error.get('code')}: "
                f"{error.get('message')}"
            )


        return data.get(
            "result"
        )


    def check_connection(
        self
    ):

        try:

            result = self._rpc_request(
                "getVersion",
                [],
                timeout=10
            )


            return {
                "connected": True,
                "version": result,
                "error": None
            }


        except Exception as e:

            return {
                "connected": False,
                "version": None,
                "error": str(e)
            }


    def get_token_supply(
        self,
        mint_address: str
    ):

        try:

            mint = self._to_pubkey(
                mint_address
            )


            result = self._rpc_request(
                "getTokenSupply",
                [
                    str(mint),
                    {
                        "commitment": "confirmed"
                    }
                ],
                timeout=15
            )


            value = result[
                "value"
            ]


            amount = int(
                value[
                    "amount"
                ]
            )


            decimals = int(
                value[
                    "decimals"
                ]
            )


            ui_amount = (
                amount
                / (
                    10
                    ** decimals
                )
                if decimals > 0
                else float(amount)
            )


            return {
                "success": True,
                "amount": amount,
                "decimals": decimals,
                "ui_amount": ui_amount,
                "error": None
            }


        except Exception as e:

            return {
                "success": False,
                "amount": 0,
                "decimals": 0,
                "ui_amount": 0.0,
                "error": str(e)
            }


    def get_signatures_for_address(
        self,
        address: str,
        limit: int = 20
    ):

        try:

            pubkey = self._to_pubkey(
                address
            )


            limit = max(
                1,
                min(
                    int(limit),
                    100
                )
            )


            result = self._rpc_request(
                "getSignaturesForAddress",
                [
                    str(pubkey),
                    {
                        "limit": limit,
                        "commitment": "confirmed"
                    }
                ],
                timeout=15
            )


            signatures = []


            for item in result:

                signatures.append(
                    {
                        "signature": item.get(
                            "signature"
                        ),
                        "slot": item.get(
                            "slot"
                        ),
                        "block_time": item.get(
                            "blockTime"
                        ),
                        "err": item.get(
                            "err"
                        )
                    }
                )


            return {
                "success": True,
                "signatures": signatures,
                "count": len(
                    signatures
                ),
                "error": None
            }


        except Exception as e:

            return {
                "success": False,
                "signatures": [],
                "count": 0,
                "error": str(e)
            }


    def get_transaction(
        self,
        signature: str
    ):

        try:

            result = self._rpc_request(
                "getTransaction",
                [
                    signature,
                    {
                        "encoding": "jsonParsed",
                        "commitment": "confirmed",
                        "maxSupportedTransactionVersion": 0
                    }
                ],
                timeout=15
            )


            if result is None:

                return {
                    "success": False,
                    "transaction": None,
                    "error": "Transaction not found"
                }


            return {
                "success": True,
                "transaction": result,
                "error": None
            }


        except Exception as e:

            return {
                "success": False,
                "transaction": None,
                "error": str(e)
            }


    def extract_wallet_changes(
        self,
        transaction: dict,
        mint_address: str
    ):

        try:

            meta = (
                transaction.get(
                    "meta"
                )
                or {}
            )


            tx = (
                transaction.get(
                    "transaction"
                )
                or {}
            )


            message = (
                tx.get(
                    "message"
                )
                or {}
            )


            account_keys = (
                message.get(
                    "accountKeys"
                )
                or []
            )


            signer_wallets = []


            for item in account_keys:

                if isinstance(
                    item,
                    dict
                ):

                    pubkey = item.get(
                        "pubkey"
                    )

                    signer = item.get(
                        "signer",
                        False
                    )


                else:

                    pubkey = item
                    signer = False


                if (
                    signer
                    and pubkey
                ):

                    signer_wallets.append(
                        pubkey
                    )


            pre_token = (
                meta.get(
                    "preTokenBalances"
                )
                or []
            )


            post_token = (
                meta.get(
                    "postTokenBalances"
                )
                or []
            )


            token_before = {}
            token_after = {}


            for item in pre_token:

                if (
                    item.get(
                        "mint"
                    )
                    != mint_address
                ):
                    continue


                owner = item.get(
                    "owner"
                )


                ui_amount = (
                    item
                    .get(
                        "uiTokenAmount",
                        {}
                    )
                    .get(
                        "uiAmount"
                    )
                )


                if owner:

                    token_before[
                        owner
                    ] = float(
                        ui_amount
                        or 0
                    )


            for item in post_token:

                if (
                    item.get(
                        "mint"
                    )
                    != mint_address
                ):
                    continue


                owner = item.get(
                    "owner"
                )


                ui_amount = (
                    item
                    .get(
                        "uiTokenAmount",
                        {}
                    )
                    .get(
                        "uiAmount"
                    )
                )


                if owner:

                    token_after[
                        owner
                    ] = float(
                        ui_amount
                        or 0
                    )


            pre_balances = (
                meta.get(
                    "preBalances"
                )
                or []
            )


            post_balances = (
                meta.get(
                    "postBalances"
                )
                or []
            )


            changes = []


            for wallet in signer_wallets:

                token_change = (
                    token_after.get(
                        wallet,
                        0.0
                    )
                    -
                    token_before.get(
                        wallet,
                        0.0
                    )
                )


                if token_change == 0:
                    continue


                sol_change = 0.0


                for index, item in enumerate(
                    account_keys
                ):

                    if isinstance(
                        item,
                        dict
                    ):

                        pubkey = item.get(
                            "pubkey"
                        )


                    else:

                        pubkey = item


                    if pubkey != wallet:
                        continue


                    if (
                        index
                        < len(
                            pre_balances
                        )
                        and
                        index
                        < len(
                            post_balances
                        )
                    ):

                        sol_change = (
                            post_balances[
                                index
                            ]
                            -
                            pre_balances[
                                index
                            ]
                        ) / 1_000_000_000


                    break


                changes.append(
                    {
                        "wallet_address": wallet,
                        "token_change": token_change,
                        "sol_change": sol_change
                    }
                )


            return {
                "success": True,
                "changes": changes,
                "count": len(
                    changes
                ),
                "error": None
            }


        except Exception as e:

            return {
                "success": False,
                "changes": [],
                "count": 0,
                "error": str(e)
            }


    def _fetch_transaction_bundle(
        self,
        signature_item: dict,
        mint_address: str
    ):

        if signature_item.get(
            "err"
        ) is not None:

            return []


        signature = signature_item.get(
            "signature"
        )


        if not signature:
            return []


        tx_result = self.get_transaction(
            signature
        )


        if not tx_result[
            "success"
        ]:

            return []


        changes = self.extract_wallet_changes(
            tx_result[
                "transaction"
            ],
            mint_address
        )


        if not changes[
            "success"
        ]:

            return []


        output = []


        for change in changes[
            "changes"
        ]:

            activity = dict(
                change
            )


            activity[
                "signature"
            ] = signature


            activity[
                "block_time"
            ] = signature_item.get(
                "block_time"
            )


            output.append(
                activity
            )


        return output


    def get_recent_wallet_activity(
        self,
        mint_address: str,
        limit: int = 20,
        max_workers: int = 8
    ):

        signatures = (
            self.get_signatures_for_address(
                mint_address,
                limit=limit
            )
        )


        if not signatures[
            "success"
        ]:

            return {
                "success": False,
                "activities": [],
                "count": 0,
                "error": signatures[
                    "error"
                ]
            }


        valid_items = [
            item
            for item
            in signatures[
                "signatures"
            ]
            if item.get(
                "err"
            ) is None
        ]


        activities = []


        max_workers = max(
            1,
            min(
                int(max_workers),
                12
            )
        )


        with ThreadPoolExecutor(
            max_workers=max_workers
        ) as executor:

            futures = [
                executor.submit(
                    self._fetch_transaction_bundle,
                    item,
                    mint_address
                )
                for item
                in valid_items
            ]


            for future in as_completed(
                futures
            ):

                try:

                    items = (
                        future.result()
                    )


                    activities.extend(
                        items
                    )


                except Exception:

                    continue


        return {
            "success": True,
            "activities": activities,
            "count": len(
                activities
            ),
            "error": None
        }