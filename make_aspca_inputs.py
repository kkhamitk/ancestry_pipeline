__author__ = 'armartin'
#takes in rephased alleles rfmix Viterbi file and outputs ASPCA inputs files

import argparse
import os
import gzip

def open_file(filename):
    if filename.endswith('gz'):
        my_file = gzip.open(filename)
    else:
        my_file = open(filename)
    return my_file

def main(args):
    ## find admixed versus reference panel individuals
    ind_order = []
    all_inds = []
    sample = open_file(args.sample)
    classes = open_file(args.classes)
    classes = classes.readline().strip().split()
    classes = classes[0::2] #get odds
    i = 0
    ind_class = {}
    
    keep = set()# get rid of this as requirement.
    if args.keep is not None:
        filtered = open_file(args.keep)#
        for line in filtered:#
            keep.add(line.strip())#
    
    ## get all admixed samples
    for line in sample:
        line = line.strip()
        all_inds.append(line)
        ind_class[line] = classes[i]
        #if (line.startswith('SA') and line in keep) or not line.startswith('SA'):#this might mess up a lot of things
        #    ind_order.append(line)
        #if classes[i] == '3' and line.startswith('SA'):
        #    ind_class[line] = '0'
        #else:
        #    ind_class[line] = classes[i]
        i += 1
    
    print ind_order#
    print ind_class
    
    ## write beagle header files for admixed and ancestral beagle files
    out_anc = open(args.out + '_anc.beagle', 'w')
    out_adm = open(args.out + '_adm.beagle', 'w')
    out_anc.write('I\tid\t')
    out_adm.write('I\tid\t')
    vit_all = {}
    vit_prob = {}
    for ind in all_inds:
        if ind_class[ind] == '0':
            out_adm.write(ind + '_A\t' + ind + '_B\t')
        else:
            out_anc.write(ind + '_A\t' + ind + '_B\t')
    out_adm.write('\n')
    out_anc.write('\n')
    
    def check_anc(anc): #TO DO: take in a number corresponding to the ancestral class of interest
        sum_anc = 0
        for i in range(2,len(anc)):
            sum_anc += int(anc[i])
        if sum_anc == (len(anc) - 2) or sum_anc == 0:
            #print 'monomorphic'
            #print anc
            return False
        else:
            return True
    
    def chunker(seq, size):
        return (seq[pos:pos + size] for pos in xrange(0, len(seq), size))
    
    #write all markers that are not monomorphic in reference panel
    haps = open_file(args.haps)
    alleles = open_file(args.alleles)
    vit = open_file(args.vit)
    fbk = open_file(args.vit.replace('Viterbi.txt', 'ForwardBackward.txt'))
    out_vit = open(args.out + '.vit', 'w')
    out_markers = open(args.out + '.markers', 'w')
    marker_count = 0
    for line in haps:
        line = line.strip().split()
        markers = alleles.readline().strip().split()
        vit_line = vit.readline().strip().split()
        fbk_line = fbk.readline().strip().split()
        fbk_chunked = chunker(fbk_line, 3)
        max_chunks = []
        for chunk in fbk_chunked:
            max_chunks.append(max(map(float, chunk)))
        #print line
        #print markers
        anc = ['M', line[2]]
        adm = ['M', line[2]]
        i=0
        #print markers[0]
        #print vit_line
        anc_mono = []
        for ind in all_inds: #this would be a problem because indexing is off
            if ind in ind_order:
                if ind_class[ind] == '0':
                #if ind_class[ind] == '0' and ind in keep:
                    adm.append(markers[0][i])
                    adm.append(markers[0][i+1])
                else:
                #elif ind.startswith('SA') and ind in keep:
                    anc.append(markers[0][i])
                    anc.append(markers[0][i+1])
                    if args.mono_class is not None and ind_class[ind] == args.mono_class:
                        anc_mono.append(markers[0][i])
                        anc_mono.append(markers[0][i+1])
            i += 2
        i=0
        multimorphic = (check_anc(anc_mono) if anc_mono != [] else check_anc(anc))
        if multimorphic: #by default, check all for monomorphic, alternative, check subset for monomorphic
            for ind in all_inds:
                if ind in ind_order:
                    #print ind + ' ' + vit_line[i]
                    if max_chunks[i] > args.fbk_threshold:
                        vit_all[ind + '_A'].append(vit_line[i])
                    else:
                        vit_all[ind + '_A'].append('-9')
                    if max_chunks[i+1] > args.fbk_threshold:
                        vit_all[ind + '_B'].append(vit_line[i+1])
                    else:
                        vit_all[ind + '_B'].append('-9')
                i += 2
            out_adm.write('\t'.join(adm) + '\n')
            out_anc.write('\t'.join(anc) + '\n')
            out_markers.write('window' + str(marker_count) + '\t' + line[2] + '\n')
            marker_count += 1
        
    for ind in ind_order:
        out_vit.write(ind + '_A ' + ' '.join(vit_all[ind + '_A']) + '\n')
        out_vit.write(ind + '_B ' + ' '.join(vit_all[ind + '_B']) + '\n')
    
    out_adm.close()
    out_anc.close()
    out_vit.close()

if __name__ == '__main__':    
    parser = argparse.ArgumentParser()
    parser.add_argument('--alleles', help='alleles file produced by RFMix', required=True)
    parser.add_argument('--vit', help='viterbi file produced by RFMix', required=True)
    parser.add_argument('--haps', required=True)
    parser.add_argument('--sample', required=True)
    parser.add_argument('--classes', required=True)
    parser.add_argument('--out', required=True)
    
    parser.add_argument('--fbk_threshold', default=0.99, type=float)
    parser.add_argument('--mono_class')
    parser.add_argument('--keep')
    
    args = parser.parse_args()
    main(args)