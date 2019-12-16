# Requirements:
# pip install helios-web3
# pip install py-helios-solc
# pip install eth-keys
# pip install eth-keyfile
#

from eth_keys import keys
import eth_keyfile
from eth_utils import to_checksum_address, encode_hex
from helios_web3 import HeliosWeb3 as Web3
from helios_web3 import IPCProvider, WebsocketProvider
from helios_web3.utils.block_creation import prepare_and_sign_block
from helios_solc import install_solc, compile_files
import time

W3_TX_DEFAULTS = {'gas': 0, 'gasPrice': 0, 'chainId': 0}

#
# First we compile our solidity file.
#

# First install the solidity binary v100.5.12 and above is helios solc
from hvm.constants import CREATE_CONTRACT_ADDRESS

install_solc('v100.5.12')

# Next, compile your file. We will compile the delegated token contract
solidity_file = '../../smart_contracts/solidity/delegated_token.sol'
contract_name = 'HeliosDelegatedToken'
compiled_sol = compile_files([solidity_file])

# get the contract interface. This contains the binary, the abi etc...
contract_interface = compiled_sol['{}:{}'.format(solidity_file, contract_name)]







#
# Next, we interact with the contract. Lets check the balance on the chain that deployed the contract.
#

# Websocket URL for hypothesis testnet bootnode. If you change this to mainnet, make sure you change network id too.
websocket_url = 'wss://hypothesis1.heliosprotocol.io:30304'
network_id = 42

# Use this code to load a private key from a keystore file. You will deploy the contract from this account
# We have provided a test keystore file that may contain a small amount of testnet HLS. But you should replace it
# with your own.
keystore_path = 'test_keystore.txt' # path to your keystore file
keystore_password = 'LVTxfhwY4PvUEK8h' # your keystore password
private_key = keys.PrivateKey(eth_keyfile.extract_key_from_keyfile(keystore_path, keystore_password))

deployed_contract_address = '0xa5df294e3ee433b748d7cfc9814112fc5ae5bd27' # Replace this with the address of your contract
deployer_wallet_address = private_key.public_key.to_checksum_address()

# Create web3
w3 = Web3(WebsocketProvider(websocket_url))

# Create the web3 contract factory
HeliosDelegatedToken = w3.hls.contract(
    address=to_checksum_address(deployed_contract_address),
    abi=contract_interface['abi'],
)

# Build transaction to deploy the contract.

transaction = {
                'from': deployer_wallet_address,
                'to': deployer_wallet_address,
                'codeAddress': deployed_contract_address # The code address tells it where the smart contract code is.
            }

balance = HeliosDelegatedToken.caller(transaction=transaction).getBalance()

print("The balance on chain {} before the transfer is {}".format(deployer_wallet_address, balance))







#
# Next, lets transfer some tokens to another chain
#

# Create a new account to send it to
new_account = w3.hls.account.create()
new_private_key = new_account._key_obj

amount_to_transfer = 1000

w3_tx1 = HeliosDelegatedToken.functions.transfer(amount_to_transfer).buildTransaction(W3_TX_DEFAULTS)

transaction = {
                'to': new_private_key.public_key.to_canonical_address(),
                'gas': 20000000, #make sure this is enough to cover deployment
                'value': 0,
                'chainId': network_id,
                'data': w3_tx1['data'],
                'codeAddress': deployed_contract_address, # The code address tells it where the smart contract code is.
                'executeOnSend': True, # Helios Delegated Tokens require executeOnSend = True for transfering tokens
            }

# Give the transaction the correct nonce and prepare the header
signed_block, header_dict, transactions = prepare_and_sign_block(w3, private_key, [transaction])

# Send it to the network
response = w3.hls.sendRawBlock(signed_block['rawBlock'])

print("Sending {} tokens from {} to {}".format(amount_to_transfer, deployer_wallet_address, new_private_key.public_key.to_checksum_address()))







#
# Receive the transaction on the chain we sent it to
#
# Get receivable transactions from the node
receivable_transactions = w3.hls.getReceivableTransactions(new_private_key.public_key.to_canonical_address())

# Prepare the header
signed_block, header_dict, transactions = prepare_and_sign_block(w3, new_private_key, receivable_transactions = receivable_transactions)

# Send it to the network
response = w3.hls.sendRawBlock(signed_block['rawBlock'])

print("Receiving tokens on chain {}".format(new_private_key.public_key.to_checksum_address()))







#
# Check the token balance on the chain you sent them to
#
transaction = {
                'from': new_private_key.public_key.to_canonical_address(),
                'to': new_private_key.public_key.to_canonical_address(),
                'codeAddress': deployed_contract_address # The code address tells it where the smart contract code is.
            }

balance = HeliosDelegatedToken.caller(transaction=transaction).getBalance()

print("The balance on chain {} is {}".format(encode_hex(new_private_key.public_key.to_canonical_address()), balance))







#
#
# After the transfer computation is received, there will be some leftover gas that gets refunded to you. Lets receive that refund back onto our chain:
#
# We must wait 10 seconds before we can add the next block
print("Waiting 10 seconds before receiving gas refund")
time.sleep(10)
# Get receivable transactions from the node
receivable_transactions = w3.hls.getReceivableTransactions(private_key.public_key.to_canonical_address())

# Prepare the header
signed_block, header_dict, transactions = prepare_and_sign_block(w3, private_key, receivable_transactions = receivable_transactions)

# Send it to the network
response = w3.hls.sendRawBlock(signed_block['rawBlock'])

print('Gas refunds received successfully')