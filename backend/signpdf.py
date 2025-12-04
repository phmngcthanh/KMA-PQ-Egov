# Import Libraries
import OpenSSL
import os
import time
import argparse
from PDFNetPython3.PDFNetPython import *
from typing import Tuple
import oqs


def createKeyPair(algorithm="DILITHIUM_3"):
    """
    Create a post-quantum key pair using the specified algorithm.
    Arguments: algorithm - Post-quantum algorithm (default: DILITHIUM_3)
    Returns: The public/private key pair as bytes
    """
    with oqs.Signature(algorithm) as sig:
        public_key = sig.generate_keypair()
        private_key = sig.export_secret_key()
    return public_key, private_key

def create_self_signed_cert(public_key):
    """Create a self-signed certificate using a post-quantum public key."""
    cert = OpenSSL.crypto.X509()
    cert.get_subject().CN = "Post-Quantum Certificate"
    cert.set_serial_number(int(time.time() * 10))
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(10 * 365 * 24 * 60 * 60)
    cert.set_pubkey(OpenSSL.crypto.load_publickey(OpenSSL.crypto.FILETYPE_PEM, public_key))
    cert.sign(OpenSSL.crypto.load_privatekey(OpenSSL.crypto.FILETYPE_PEM, private_key), 'sha256')
    return cert

def load():
    """Generate the post-quantum certificate."""
    summary = {}
    summary['OQS Version'] = oqs.get_version()
    # Generating a Post-Quantum Key Pair...
    public_key, private_key = createKeyPair()
    with open('./static/private_key.pem', 'wb') as pk:
        pk.write(private_key)
        summary['Private Key'] = private_key
    with open('./static/public_key.pem', 'wb') as pub_key:
        pub_key.write(public_key)
        summary['Public Key'] = public_key
    # Generating a self-signed certificate...
    cert = create_self_signed_cert(public_key)
    with open('./static/certificate.cer', 'wb') as cer:
        cer.write(OpenSSL.crypto.dump_certificate(OpenSSL.crypto.FILETYPE_PEM, cert))
        summary['Self Signed Certificate'] = cert
    # Done - Generating a self-signed client certification...
    # Generating the public key...
    with open('./static/public_key.pem', 'wb') as pub_key:
        pub_key_str = OpenSSL.crypto.dump_publickey(
            OpenSSL.crypto.FILETYPE_PEM, cert.get_pubkey())
        #print("Public key = ",pub_key_str)
        pub_key.write(pub_key_str)
        summary['Public Key'] = pub_key_str
    # Done - Generating the public key...
    # Take a private key and a certificate and combine them into a PKCS12 file.
    # Generating a container file of the private key and the certificate...
    p12 = OpenSSL.crypto.PKCS12()
    p12.set_privatekey(key)
    p12.set_certificate(cert)
    open('./static/container.pfx', 'wb').write(p12.export())
    # You may convert a PKSC12 file (.pfx) to a PEM format
    # Done - Generating a container file of the private key and the certificate...
    # To Display A Summary
    print("## Initialization Summary ##################################################")
    print("\n".join("{}:{}".format(i, j) for i, j in summary.items()))
    print("############################################################################")
    return True

def sign_file(input_file: str, signatureID: str, x_coordinate: int, y_coordinate: int, pages: Tuple = None, output_file: str = None):
    """Sign a PDF file using a post-quantum private key."""
    # An output file is automatically generated with the word signed added at its end
    if not output_file:
        output_file = (os.path.splitext(input_file)[0]) + "_signed.pdf"
    # Initialize the library
    PDFNet.Initialize("demo:1638635859886:7b60eaee03000000004060486b4419a9a26e0a7c518d4bba84b4c02e69")
    doc = PDFDoc(input_file)
    # Create a signature field
    sigField = SignatureWidget.Create(doc, Rect(
        x_coordinate, y_coordinate, x_coordinate+100, y_coordinate+50), signatureID)
    # Iterate throughout document pages
    for page in range(1, (doc.GetPageCount() + 1)):
        # If required for specific pages
        if pages and str(page) not in pages:
            continue
        pg = doc.GetPage(page)
        # Create a signature text field and push it on the page
        pg.AnnotPushBack(sigField)
    # Signature image
    sign_filename = os.path.dirname(
        os.path.abspath(__file__)) + "/static/signature.jpg"
    pk_filename = os.path.dirname(
        os.path.abspath(__file__)) + "/static/private_key.pem"
    # Retrieve the signature field.
    approval_field = doc.GetField(signatureID)
    approval_signature_digsig_field = DigitalSignatureField(approval_field)
    # Add appearance to the signature field.
    print(sign_filename)
    img = Image.Create(doc.GetSDFDoc(), sign_filename)
    found_approval_signature_widget = SignatureWidget(approval_field.GetSDFObj())
    found_approval_signature_widget.CreateSignatureAppearance(img)
    # Prepare the signature and signature handler for signing.
    approval_signature_digsig_field.SignOnNextSave(pk_filename, '')
    # The signing will be done during the following incremental save operation.
    doc.Save(output_file, SDFDoc.e_incremental)
    # Develop a Process Summary
    summary = {
        "Input File": input_file, "Signature ID": signatureID, 
        "Output File": output_file, "Signature File": sign_filename, 
        "Certificate File": pk_filename
    }
    # Printing Summary
    print("## Summary ########################################################")
    print("\n".join("{}:{}".format(i, j) for i, j in summary.items()))
    print("###################################################################")
    return output_file

def sign_folder(**kwargs):
    """Sign all PDF Files within a specified path"""
    input_folder = kwargs.get('input_folder')
    signatureID = kwargs.get('signatureID')
    pages = kwargs.get('pages')
    x_coordinate = int(kwargs.get('x_coordinate'))
    y_coordinate = int(kwargs.get('y_coordinate'))
    # Run in recursive mode
    recursive = kwargs.get('recursive')
    # Loop though the files within the input folder.
    for foldername, dirs, filenames in os.walk(input_folder):
        for filename in filenames:
            # Check if pdf file
            if not filename.endswith('.pdf'):
                continue
            # PDF File found
            inp_pdf_file = os.path.join(foldername, filename)
            print("Processing file =", inp_pdf_file)
            # Compress Existing file
            sign_file(input_file=inp_pdf_file, signatureID=signatureID, x_coordinate=x_coordinate,
                      y_coordinate=y_coordinate, pages=pages, output_file=None)
        if not recursive:
            break

def is_valid_path(path):
    """Validates the path inputted and checks whether it is a file path or a folder path"""
    if not path:
        raise ValueError(f"Invalid Path")
    if os.path.isfile(path):
        return path
    elif os.path.isdir(path):
        return path
    else:
        raise ValueError(f"Invalid Path {path}")


def parse_args():
    """Get user command line parameters"""
    # -i ./Sign/mau.pdf -s 10001 -p 1 -x 100 -y 210
    parser = argparse.ArgumentParser(description="Available Options")
    parser.add_argument('-l', '--load', dest='load', action="store_true",
                        help="Load the required configurations and create the certificate")
    parser.add_argument('-i', '--input_path', dest='input_path', type=is_valid_path,
                        help="Enter the path of the file or the folder to process")
    parser.add_argument('-s', '--signatureID', dest='signatureID',
                        type=str, help="Enter the ID of the signature")
    parser.add_argument('-p', '--pages', dest='pages', type=tuple,
                        help="Enter the pages to consider e.g.: [1,3]")
    parser.add_argument('-x', '--x_coordinate', dest='x_coordinate',
                        type=int, help="Enter the x coordinate.")
    parser.add_argument('-y', '--y_coordinate', dest='y_coordinate',
                        type=int, help="Enter the y coordinate.")
    path = parser.parse_known_args()[0].input_path
    if path and os.path.isfile(path):
        parser.add_argument('-o', '--output_file', dest='output_file',
                            type=str, help="Enter a valid output file")
    if path and os.path.isdir(path):
        parser.add_argument('-r', '--recursive', dest='recursive', default=False, type=lambda x: (
            str(x).lower() in ['true', '1', 'yes']), help="Process Recursively or Non-Recursively")
    args = vars(parser.parse_args())
    # To Display The Command Line Arguments
    print("## Command Arguments #################################################")
    print("\n".join("{}:{}".format(i, j) for i, j in args.items()))
    print("######################################################################")
    return args

if __name__ == '__main__':
    # Parsing command line arguments entered by user
    args = parse_args()
    if args['load'] == True:
        load()
    else:
        # If File Path
        if os.path.isfile(args['input_path']):
            sign_file(
                input_file=args['input_path'], signatureID=args['signatureID'],
                x_coordinate=int(args['x_coordinate']), y_coordinate=int(args['y_coordinate']), 
                pages=args['pages'], output_file=args['output_file']
            )
        # If Folder Path
        elif os.path.isdir(args['input_path']):
            # Process a folder
            sign_folder(
                input_folder=args['input_path'], signatureID=args['signatureID'], 
                x_coordinate=int(args['x_coordinate']), y_coordinate=int(args['y_coordinate']),
                pages=args['pages'], recursive=args['recursive']
            )