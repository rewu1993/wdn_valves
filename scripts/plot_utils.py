from shapely.geometry import Point, LineString
import pandas as pd
import geopandas as gpd
import networkx as nx


def get_pipe_df(wn):
    G = wn.get_graph()
    pos = nx.get_node_attributes(G,'pos')

    lines = []
    pcost_list = []
    dcost_list = []
    for pipe_name in wn.pipe_name_list:
        pipe = wn.get_link(pipe_name)  
        start_node = pipe.start_node_name
        end_node = pipe.end_node_name

        loc_start = pos[start_node]
        loc_end = pos[end_node]
        l = LineString([Point(loc_start), Point(loc_end)])
        lines.append(l)
        
    df_dict = {'pipe_names':wn.pipe_name_list,
              'geometry':lines}
    df = pd.DataFrame.from_dict(df_dict)
    gdf = gpd.GeoDataFrame(df, geometry='geometry')
    return gdf


def plot_neighbor_pipe_selection(base_cluster,pname,pnames_list):
    base =  pipe_data[pipe_data['pipe_names'] .isin(base_cluster)]
    cluster0 = pipe_data[pipe_data['pipe_names'] == pname]
    clusters = []
    for pnames in pnames_list:
        cluster = pipe_data[pipe_data['pipe_names'].isin(pnames)]
        clusters.append(cluster)
    
    ax1 = base.plot(figsize = (18,10),
                         linewidth=1,
                        color = 'black',
                        alpha = 0.5)
    colors = sns.color_palette()
    for i, cluster in enumerate(clusters):
        ax1 = cluster.plot(ax= ax1,
                            linewidth=2,
                           label = f'Size {len(pnames_list[i])}',
                           color = colors[i],
                            alpha = 1)
        
    ax1 = cluster0.plot(ax= ax1,
                         linewidth=3,
                        color = 'red',
                        label = 'Selected Pipe',
                        alpha = 1)
    ax1.legend()
    ax1.axis('off')
    ax1.plot()
    ax1.figure.savefig("figures/bundel_example.png",dpi=300,bbox_inches='tight')
    
def get_pcluster(pid,pipe_adj_mtx,required_num,source_pids):
    black_list = copy.deepcopy(source_pids)
    neighber_num = required_num-1
    pids_cluster = get_neighbor_pids(pid,pipe_adj_mtx,
                                             neighber_num,black_list)+[pid]    
    pnames_cluster = [lid2lname[pid] for pid in pids_cluster]
    return pnames_cluster
