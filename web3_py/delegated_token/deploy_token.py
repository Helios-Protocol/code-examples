# Requirements:
# pip install helios-web3
# pip install py-helios-solc
# pip install eth-keys
# pip install eth-keyfile
# pip install py-helios-node
# pip install eth-utils
#
# Also make sure you have some testnet HLS in your account using our faucet at https://heliosprotocol.io/faucet
#
import time
from eth_keys import keys
import eth_keyfile
from helios_web3 import HeliosWeb3 as Web3
from helios_web3 import IPCProvider, WebsocketProvider
from helios_web3.utils.block_creation import prepare_and_sign_block

from helios_solc import install_solc, compile_files

from hvm.utils.address import generate_contract_address
from eth_utils import encode_hex

from hvm.constants import CREATE_CONTRACT_ADDRESS

W3_TX_DEFAULTS = {'gas': 0, 'gasPrice': 0, 'chainId': 0}

#
# First we compile our solidity file.
#

# First install the solidity binary v100.5.12 and above is helios solc


install_solc('v100.5.12')

# Next, compile your file. We will compile the delegated token contract
solidity_file = '../../smart_contracts/solidity/delegated_token.sol'
contract_name = 'HeliosDelegatedToken'
compiled_sol = compile_files([solidity_file])

# get the contract interface. This contains the binary, the abi etc...
contract_interface = compiled_sol['{}:{}'.format(solidity_file, contract_name)]


#
# Next, we deploy the compiled contract to the network
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

# Create web3
w3 = Web3(WebsocketProvider(websocket_url))

# Create the web3 contract factory
HeliosDelegatedToken = w3.hls.contract(
    abi=contract_interface['abi'],
    bytecode=contract_interface['bin']
)

# Build transaction to deploy the contract.
w3_tx1 = HeliosDelegatedToken.constructor().buildTransaction(W3_TX_DEFAULTS)


transaction = {
                'to': CREATE_CONTRACT_ADDRESS,
                'gas': 20000000, #make sure this is enough to cover deployment
                'value': 0,
                'chainId': network_id,
                'data': w3_tx1['data']
            }

# Give the transaction the correct nonce and prepare the header
signed_block, header_dict, transactions = prepare_and_sign_block(w3, private_key, [transaction])

# Send it to the network
response = w3.hls.sendRawBlock(signed_block['rawBlock'])

# Done! Your contract is now deployed.

# How do I figure out the deployed contract address?
deployed_contract_address = generate_contract_address(private_key.public_key.to_canonical_address(), transactions[0]['nonce'])
print("Contract deployed to address {}".format(encode_hex(deployed_contract_address)))







#
# After the deploy takes place, it will send us a new transaction to mint the tokens on our chain. Lets receive that transaction
#
# We must wait 10 seconds before we can add the next block
print("Waiting 10 seconds before adding new block")
time.sleep(10)
# Get receivable transactions from the node
receivable_transactions = w3.hls.getReceivableTransactions(private_key.public_key.to_canonical_address())

# Prepare the header
signed_block, header_dict, transactions = prepare_and_sign_block(w3, private_key, receivable_transactions = receivable_transactions)

# Send it to the network
response = w3.hls.sendRawBlock(signed_block['rawBlock'])

print('Transaction received successfully!')